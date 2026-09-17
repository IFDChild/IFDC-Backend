from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


ALLOWED_STATUSES = {"new", "contacted", "closed"}


class DonationInterestCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = Field(default=None, max_length=255)
    # Honeypot: real visitors never see or fill this field.
    website: Optional[str] = Field(default=None, max_length=255)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        if value is None:
            return None
        value = " ".join(value.split())
        return value or None


class DonationInterestUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=5000)

    @field_validator("status")
    @classmethod
    def known_status(cls, value):
        if value is None:
            return value
        value = value.strip().lower()
        if value not in ALLOWED_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}")
        return value


class DonationInterestResponse(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str]
    status: str
    notes: Optional[str]
    admin_notified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DonationInterestReceipt(BaseModel):
    message: str
