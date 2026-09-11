from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_STATUSES = {"draft", "published"}


# Audiences the website groups the resource library by.
AUDIENCES = [
    "Parents & Caregivers",
    "Educators & Schools",
    "Policymakers & Research",
    "Journalists & Media",
    "Children & Young People",
]


class ResourceCreate(BaseModel):

    title: str = Field(max_length=255)

    description: Optional[str] = None

    audience: str = Field(max_length=100)

    category: Optional[str] = Field(default=None, max_length=100)

    file_url: str = Field(max_length=500)

    file_name: Optional[str] = Field(default=None, max_length=255)

    file_size: Optional[int] = None

    thumbnail_url: Optional[str] = Field(default=None, max_length=500)

    status: str = "published"

    @field_validator("title", "file_url")
    @classmethod
    def not_blank(cls, value: str) -> str:

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("This field cannot be empty")

        return cleaned

    @field_validator("audience")
    @classmethod
    def known_audience(cls, value: str) -> str:

        cleaned = value.strip()

        if cleaned not in AUDIENCES:
            allowed = ", ".join(AUDIENCES)

            raise ValueError(f"Audience must be one of: {allowed}")

        return cleaned

    @field_validator("status")
    @classmethod
    def known_status(cls, value: str) -> str:

        cleaned = value.strip().lower()

        if cleaned not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))

            raise ValueError(f"Status must be one of: {allowed}")

        return cleaned


class ResourceUpdate(BaseModel):

    title: Optional[str] = Field(default=None, max_length=255)

    description: Optional[str] = None

    audience: Optional[str] = Field(default=None, max_length=100)

    category: Optional[str] = Field(default=None, max_length=100)

    file_url: Optional[str] = Field(default=None, max_length=500)

    file_name: Optional[str] = Field(default=None, max_length=255)

    file_size: Optional[int] = None

    thumbnail_url: Optional[str] = Field(default=None, max_length=500)

    status: Optional[str] = None

    @field_validator("audience")
    @classmethod
    def known_audience(cls, value: Optional[str]) -> Optional[str]:

        if value is None:
            return None

        cleaned = value.strip()

        if cleaned not in AUDIENCES:
            allowed = ", ".join(AUDIENCES)

            raise ValueError(f"Audience must be one of: {allowed}")

        return cleaned

    @field_validator("status")
    @classmethod
    def known_status(cls, value: Optional[str]) -> Optional[str]:

        if value is None:
            return None

        cleaned = value.strip().lower()

        if cleaned not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))

            raise ValueError(f"Status must be one of: {allowed}")

        return cleaned


class ResourceResponse(BaseModel):

    id: int

    title: str

    description: Optional[str]

    audience: str

    category: Optional[str]

    file_url: str

    file_name: Optional[str]

    file_size: Optional[int]

    thumbnail_url: Optional[str]

    status: str

    downloads: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
