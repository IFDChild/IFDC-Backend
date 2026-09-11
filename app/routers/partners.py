from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.partner import PartnerInquiry
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.partner import (
    ALLOWED_STATUSES,
    PartnerInquiryCreate,
    PartnerInquiryResponse,
    PartnerInquiryStatusUpdate
)


router = APIRouter(
    prefix="/api/partners",
    tags=["Partners"]
)


@router.post(
    "",
    response_model=PartnerInquiryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_inquiry(
    inquiry_data: PartnerInquiryCreate,
    db: Session = Depends(get_db)
):
    """Public endpoint used by the Partner With Us form."""

    inquiry = PartnerInquiry(
        organization_name=inquiry_data.organization_name,
        contact_person=inquiry_data.contact_person,
        email=inquiry_data.email.lower(),
        website=inquiry_data.website,
        partnership_type=inquiry_data.partnership_type,
        message=inquiry_data.message,
        status="new"
    )

    db.add(inquiry)

    db.commit()

    db.refresh(inquiry)

    return inquiry


@router.get(
    "",
    response_model=list[PartnerInquiryResponse]
)
def list_inquiries(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only - inquiries contain contact details."""

    query = db.query(PartnerInquiry)

    if status_filter:

        cleaned = status_filter.strip().lower()

        if cleaned not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))

            raise HTTPException(
                status_code=400,
                detail=f"Status must be one of: {allowed}"
            )

        query = query.filter(
            PartnerInquiry.status == cleaned
        )

    return (
        query
        .order_by(PartnerInquiry.created_at.desc())
        .all()
    )


@router.get(
    "/{inquiry_id}",
    response_model=PartnerInquiryResponse
)
def get_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    inquiry = (
        db.query(PartnerInquiry)
        .filter(PartnerInquiry.id == inquiry_id)
        .first()
    )

    if inquiry is None:
        raise HTTPException(
            status_code=404,
            detail="Inquiry not found"
        )

    return inquiry


@router.patch(
    "/{inquiry_id}",
    response_model=PartnerInquiryResponse
)
def update_inquiry_status(
    inquiry_id: int,
    status_data: PartnerInquiryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    inquiry = (
        db.query(PartnerInquiry)
        .filter(PartnerInquiry.id == inquiry_id)
        .first()
    )

    if inquiry is None:
        raise HTTPException(
            status_code=404,
            detail="Inquiry not found"
        )

    inquiry.status = status_data.status

    db.commit()

    db.refresh(inquiry)

    return inquiry
