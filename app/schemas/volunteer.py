from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator
)


ALLOWED_STATUSES = {
    "new",
    "reviewing",
    "accepted",
    "rejected"
}


class VolunteerApplicationCreate(BaseModel):

    first_name: str = Field(max_length=255)

    last_name: str = Field(max_length=255)

    email: EmailStr

    phone: Optional[str] = Field(
        default=None,
        max_length=50
    )

    address: str

    describes: str = Field(max_length=100)

    interests: List[str] = Field(min_length=1)

    social_media: Optional[str] = Field(
        default=None,
        max_length=500
    )

    motivation: str

    cv_url: Optional[str] = Field(
        default=None,
        max_length=500
    )

    @field_validator(
        "first_name",
        "last_name",
        "address",
        "describes",
        "motivation"
    )
    @classmethod
    def not_blank(cls, value: str) -> str:

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("This field cannot be empty")

        return cleaned

    @field_validator("phone", "social_media", "cv_url")
    @classmethod
    def empty_to_none(
        cls,
        value: Optional[str]
    ) -> Optional[str]:

        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    @field_validator("interests")
    @classmethod
    def clean_interests(
        cls,
        value: List[str]
    ) -> List[str]:

        cleaned = [
            item.strip()
            for item in value
            if item and item.strip()
        ]

        if not cleaned:
            raise ValueError(
                "Select at least one area of interest"
            )

        return cleaned


class VolunteerApplicationStatusUpdate(BaseModel):

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


class VolunteerApplicationResponse(BaseModel):

    id: int

    first_name: str

    last_name: str

    email: EmailStr

    phone: Optional[str]

    address: str

    describes: str

    interests: List[str]

    social_media: Optional[str]

    motivation: str

    cv_url: Optional[str]

    status: str

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
