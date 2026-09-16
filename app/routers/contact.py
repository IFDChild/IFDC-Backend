from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contact import ContactMessage
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.contact import (
    ALLOWED_STATUSES,
    SUBJECTS,
    ContactMessageCreate,
    ContactMessageResponse,
    ContactMessageStatusUpdate
)


router = APIRouter(
    prefix="/api/contact",
    tags=["Contact"]
)


@router.get("/subjects")
def list_subjects():
    """Subjects offered on the website contact form."""

    return {"subjects": SUBJECTS}


@router.post(
    "",
    response_model=ContactMessageResponse,
    status_code=status.HTTP_201_CREATED
)
def create_message(
    message_data: ContactMessageCreate,
    db: Session = Depends(get_db)
):
    """Public endpoint used by the Contact Us form."""

    message = ContactMessage(
        name=message_data.name,
        email=message_data.email.lower(),
        phone=message_data.phone,
        subject=message_data.subject,
        message=message_data.message,
        status="new"
    )

    db.add(message)

    db.commit()

    db.refresh(message)

    return message


@router.get(
    "",
    response_model=list[ContactMessageResponse]
)
def list_messages(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only - messages contain personal details."""

    query = db.query(ContactMessage)

    if status_filter:

        cleaned = status_filter.strip().lower()

        if cleaned not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))

            raise HTTPException(
                status_code=400,
                detail=f"Status must be one of: {allowed}"
            )

        query = query.filter(
            ContactMessage.status == cleaned
        )

    return (
        query
        .order_by(ContactMessage.created_at.desc())
        .all()
    )


@router.patch(
    "/{message_id}",
    response_model=ContactMessageResponse
)
def update_message_status(
    message_id: int,
    status_data: ContactMessageStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    message = (
        db.query(ContactMessage)
        .filter(ContactMessage.id == message_id)
        .first()
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )

    message.status = status_data.status

    db.commit()

    db.refresh(message)

    return message
