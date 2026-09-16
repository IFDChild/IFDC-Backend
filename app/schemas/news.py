from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


NEWS_CATEGORIES = [
    "Announcements",
    "Press Releases",
    "Events",
    "Partnerships",
    "Media Coverage",
]

NEWS_STATUSES = ["draft", "published"]


def _clean_status(value):
    if value is None:
        return value
    value = value.strip().lower()
    if value not in NEWS_STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(NEWS_STATUSES)}")
    return value


def _clean_category(value):
    if value in (None, ""):
        return None
    if value not in NEWS_CATEGORIES:
        raise ValueError(f"Category must be one of: {', '.join(NEWS_CATEGORIES)}")
    return value


class NewsCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    summary: Optional[str] = Field(default=None, max_length=600)
    content: str = Field(min_length=1)
    image: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = None
    status: str = "draft"

    @field_validator("title", "content")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value

    @field_validator("summary")
    @classmethod
    def strip_optional(cls, value):
        if value is None:
            return None
        return value.strip() or None

    @field_validator("status")
    @classmethod
    def valid_status(cls, value):
        return _clean_status(value)

    @field_validator("category")
    @classmethod
    def valid_category(cls, value):
        return _clean_category(value)


class NewsUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    summary: Optional[str] = Field(default=None, max_length=600)
    content: Optional[str] = None
    image: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = None
    status: Optional[str] = None

    @field_validator("title", "content")
    @classmethod
    def strip_required(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value

    @field_validator("summary")
    @classmethod
    def strip_optional(cls, value):
        if value is None:
            return None
        return value.strip() or None

    @field_validator("status")
    @classmethod
    def valid_status(cls, value):
        return _clean_status(value)

    @field_validator("category")
    @classmethod
    def valid_category(cls, value):
        return _clean_category(value)


class NewsResponse(BaseModel):
    id: int
    title: str
    slug: str
    summary: Optional[str]
    content: str
    image: Optional[str]
    category: Optional[str]
    status: str
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
