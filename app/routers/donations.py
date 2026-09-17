import html
import os
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.mailer import mail_configured, send_admin_email
from app.models.donation import DonationInterest
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.donation import (
    ALLOWED_STATUSES,
    DonationInterestCreate,
    DonationInterestReceipt,
    DonationInterestResponse,
    DonationInterestUpdate,
)


router = APIRouter(
    prefix="/api/donations",
    tags=["Donations"]
)

THANK_YOU = "Thank you! Our team will contact you by email about how you can support IFDC."

# Basic abuse protection for the public form (per client IP, in memory).
MAX_REQUESTS_PER_HOUR = 5
_requests: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def _allow(request: Request) -> bool:
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _lock:
        hits = _requests[key]
        while hits and hits[0] < now - 3600:
            hits.popleft()
        if len(hits) >= MAX_REQUESTS_PER_HOUR:
            return False
        hits.append(now)
        return True


def _notify_admin(interest_id: int) -> None:
    """Background task: email the admin and record whether it worked."""
    db = SessionLocal()
    try:
        interest = db.query(DonationInterest).filter(DonationInterest.id == interest_id).first()
        if interest is None:
            return

        admin_url = os.getenv("ADMIN_DASHBOARD_URL", "http://localhost:5181").rstrip("/")
        submitted = interest.created_at.strftime("%d %b %Y, %H:%M UTC")
        who = interest.name or "Not provided"

        text = (
            "Someone is willing to donate to IFDC.\n\n"
            f"Email: {interest.email}\n"
            f"Name: {who}\n"
            f"Submitted: {submitted}\n\n"
            "Reply to this email to contact them directly.\n"
            f"Manage donation requests: {admin_url}/donations\n"
        )
        page = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;color:#1a1c1e">
          <div style="background:#0B3D6E;color:#fff;padding:20px 24px;border-radius:12px 12px 0 0">
            <p style="margin:0;color:#FFE100;font-size:12px;font-weight:bold;letter-spacing:1px">IFDC WEBSITE</p>
            <h1 style="margin:6px 0 0;font-size:20px">New donation request</h1>
          </div>
          <div style="border:1px solid #e3e7ee;border-top:0;padding:20px 24px;border-radius:0 0 12px 12px">
            <p style="margin:0 0 16px">Someone is willing to donate to IFDC.</p>
            <table style="border-collapse:collapse;font-size:14px">
              <tr><td style="padding:4px 16px 4px 0;color:#5b6270">Email</td>
                  <td><a href="mailto:{html.escape(interest.email)}">{html.escape(interest.email)}</a></td></tr>
              <tr><td style="padding:4px 16px 4px 0;color:#5b6270">Name</td><td>{html.escape(who)}</td></tr>
              <tr><td style="padding:4px 16px 4px 0;color:#5b6270">Submitted</td><td>{submitted}</td></tr>
            </table>
            <p style="margin:20px 0 0;font-size:14px">Reply to this email to contact them directly, or
              <a href="{html.escape(admin_url)}/donations">manage donation requests</a>.</p>
          </div>
        </div>
        """

        sent = send_admin_email(
            subject=f"New donation request from {interest.email}",
            text=text,
            html=page,
            reply_to=interest.email,
        )
        interest.admin_notified = sent
        db.commit()
    finally:
        db.close()


def _get_or_404(interest_id: int, db: Session) -> DonationInterest:
    interest = db.query(DonationInterest).filter(DonationInterest.id == interest_id).first()
    if interest is None:
        raise HTTPException(status_code=404, detail="Donation request not found")
    return interest


@router.post(
    "",
    response_model=DonationInterestReceipt,
    status_code=status.HTTP_201_CREATED
)
def register_interest(
    payload: DonationInterestCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Public: a visitor leaves their email to say they are willing to donate."""

    # Bots fill the hidden field - pretend success, store nothing.
    if payload.website:
        return DonationInterestReceipt(message=THANK_YOU)

    if not _allow(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )

    # Same address already waiting in the last day - don't duplicate or re-email.
    recent = (
        db.query(DonationInterest)
        .filter(
            DonationInterest.email == payload.email,
            DonationInterest.status == "new",
            DonationInterest.created_at >= datetime.utcnow() - timedelta(days=1),
        )
        .first()
    )
    if recent is not None:
        if payload.name and not recent.name:
            recent.name = payload.name
            db.commit()
        return DonationInterestReceipt(message=THANK_YOU)

    interest = DonationInterest(email=payload.email, name=payload.name, status="new")
    db.add(interest)
    db.commit()
    db.refresh(interest)

    background_tasks.add_task(_notify_admin, interest.id)

    return DonationInterestReceipt(message=THANK_YOU)


@router.get("/email-status")
def email_status(current_user: User = Depends(get_current_user)):
    """Admin: whether notification emails can be sent."""
    return {"configured": mail_configured()}


@router.get("", response_model=list[DonationInterestResponse])
def list_interests(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(DonationInterest)
    if status_filter:
        cleaned = status_filter.strip().lower()
        if cleaned not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}")
        query = query.filter(DonationInterest.status == cleaned)
    return query.order_by(DonationInterest.created_at.desc()).all()


@router.patch("/{interest_id}", response_model=DonationInterestResponse)
def update_interest(
    interest_id: int,
    payload: DonationInterestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    interest = _get_or_404(interest_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interest, field, value)
    db.commit()
    db.refresh(interest)
    return interest


@router.post("/{interest_id}/resend-notification", response_model=DonationInterestResponse)
def resend_notification(
    interest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: retry the notification email (e.g. after configuring SMTP)."""
    _get_or_404(interest_id, db)
    if not mail_configured():
        raise HTTPException(status_code=400, detail="Email is not configured on the server (SMTP settings missing).")
    _notify_admin(interest_id)
    db.expire_all()
    return _get_or_404(interest_id, db)


@router.delete("/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interest(
    interest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    interest = _get_or_404(interest_id, db)
    db.delete(interest)
    db.commit()
