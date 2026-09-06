from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BlogCreate(BaseModel):

    title: str

    excerpt: Optional[str] = None

    content: str

    featured_image: Optional[str] = None

    author: Optional[str] = None

    category: Optional[str] = None

   

    status: str = "draft"


class BlogUpdate(BaseModel):

    title: Optional[str] = None

    excerpt: Optional[str] = None

    content: Optional[str] = None

    featured_image: Optional[str] = None

    author: Optional[str] = None

    category: Optional[str] = None

   

    status: Optional[str] = None


class BlogResponse(BaseModel):

    id: int

    title: str

    slug: str

    excerpt: Optional[str]

    content: str

    featured_image: Optional[str]

    author: Optional[str]

    category: Optional[str]

    

    status: str

    published_at: Optional[datetime]

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )