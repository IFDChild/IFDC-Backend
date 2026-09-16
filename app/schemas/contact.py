from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator
)


ALLOWED_STATUSES = {
    "new",
    "in_progress",
    "resolved"
}


SUBJECTS = [
    "General enquiry",
    "Report a concern",
    "Media enquiry",
    "Partnerships",
    "Volunteering",
    "Training & workshops",
]


class ContactMessageCreate(BaseModel):

    name: str = Field(max_length=255)

    email: EmailStr

    phone: Optional[str] = Field(
        default=None,
        max_length=50
    )

    subject: str = Field(max_length=100)

    message: str

    @field_validator("name", "message")
    @classmethod
    def not_blank(cls, value: str) -> str:

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("This field cannot be empty")

        return cleaned

    @field_validator("phone")
    @classmethod
    def empty_to_none(
        cls,
        value: Optional[str]
    ) -> Optional[str]:

        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    @field_validator("subject")
    @classmethod
    def known_subject(cls, value: str) -> str:

        cleaned = value.strip()

        if cleaned not in SUBJECTS:
            allowed = ", ".join(SUBJECTS)

            raise ValueError(
                f"Subject must be one of: {allowed}"
            )

        return cleaned


class ContactMessageStatusUpdate(BaseModel):

    status: str

    @field_validator("status")
    @classmethod
    def known_status(cls, value: str) -> str:

        cleaned = value.strip().lower()

        if cleaned not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))

            raise ValueError(
                f"Status must be one of: {allowed}"
            )

        return cleaned


class ContactMessageResponse(BaseModel):

    id: int

    name: str

    email: EmailStr

    phone: Optional[str]

    subject: str

    message: str

    status: str

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
