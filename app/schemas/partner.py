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
    "reviewing",
    "accepted",
    "rejected"
}


PARTNERSHIP_TYPES = {
    "Corporate & CSR Partners",
    "Government & Policy Partners",
    "Schools & Educators",
    "Media & Creative Partners",
    "NGOs & International Organizations",
    "Individual Donors & Volunteers"
}


class PartnerInquiryCreate(BaseModel):

    organization_name: str = Field(max_length=255)

    contact_person: str = Field(max_length=255)

    email: EmailStr

    website: Optional[str] = Field(
        default=None,
        max_length=500
    )

    partnership_type: str = Field(max_length=100)

    message: str

    @field_validator(
        "organization_name",
        "contact_person",
        "message"
    )
    @classmethod
    def not_blank(cls, value: str) -> str:

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("This field cannot be empty")

        return cleaned

    @field_validator("website")
    @classmethod
    def empty_to_none(
        cls,
        value: Optional[str]
    ) -> Optional[str]:

        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    @field_validator("partnership_type")
    @classmethod
    def known_type(cls, value: str) -> str:

        cleaned = value.strip()

        if cleaned not in PARTNERSHIP_TYPES:
            allowed = ", ".join(sorted(PARTNERSHIP_TYPES))

            raise ValueError(
                f"Partnership type must be one of: {allowed}"
            )

        return cleaned


class PartnerInquiryStatusUpdate(BaseModel):

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


class PartnerInquiryResponse(BaseModel):

    id: int

    organization_name: str

    contact_person: str

    email: EmailStr

    website: Optional[str]

    partnership_type: str

    message: str

    status: str

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
