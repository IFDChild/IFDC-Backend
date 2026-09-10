from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.volunteer import VolunteerApplication
from app.routers.auth import get_current_user
from app.schemas.volunteer import (
    ALLOWED_STATUSES,
    VolunteerApplicationCreate,
    VolunteerApplicationResponse,
    VolunteerApplicationStatusUpdate
)


router = APIRouter(
    prefix="/api/volunteers",
    tags=["Volunteers"]
)


@router.post(
    "",
    response_model=VolunteerApplicationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_application(
    application_data: VolunteerApplicationCreate,
    db: Session = Depends(get_db)
):
    """Public endpoint used by the website volunteer form."""

    application = VolunteerApplication(
        first_name=application_data.first_name,
        last_name=application_data.last_name,
        email=application_data.email.lower(),
        phone=application_data.phone,
        address=application_data.address,
        describes=application_data.describes,
        interests=application_data.interests,
        social_media=application_data.social_media,
        motivation=application_data.motivation,
        cv_url=application_data.cv_url,
        status="new"
    )

    db.add(application)

    db.commit()

    db.refresh(application)

    return application


@router.get(
    "",
    response_model=list[VolunteerApplicationResponse]
)
def list_applications(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only - applications contain personal data."""

    query = db.query(VolunteerApplication)

    if status_filter:

        cleaned = status_filter.strip().lower()

        if cleaned not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))

            raise HTTPException(
                status_code=400,
                detail=f"Status must be one of: {allowed}"
            )

        query = query.filter(
            VolunteerApplication.status == cleaned
        )

    return (
        query
        .order_by(VolunteerApplication.created_at.desc())
        .all()
    )


@router.get(
    "/{application_id}",
    response_model=VolunteerApplicationResponse
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    application = (
        db.query(VolunteerApplication)
        .filter(VolunteerApplication.id == application_id)
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    return application


@router.patch(
    "/{application_id}",
    response_model=VolunteerApplicationResponse
)
def update_application_status(
    application_id: int,
    status_data: VolunteerApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    application = (
        db.query(VolunteerApplication)
        .filter(VolunteerApplication.id == application_id)
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    application.status = status_data.status

    db.commit()

    db.refresh(application)

    return application
