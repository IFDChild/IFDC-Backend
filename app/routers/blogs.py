from datetime import datetime
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.blog import Blog
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.blog import (
    BlogCreate,
    BlogUpdate,
    BlogResponse
)


router = APIRouter(
    prefix="/api/blogs",
    
)


def create_slug(title: str) -> str:

    slug = title.lower()

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        slug
    )

    return slug.strip("-")


def unique_slug(
    title: str,
    db: Session,
    blog_id=None
):

    base_slug = create_slug(title)

    slug = base_slug

    counter = 1

    while True:

        query = db.query(Blog).filter(
            Blog.slug == slug
        )

        if blog_id:
            query = query.filter(
                Blog.id != blog_id
            )

        if not query.first():
            return slug

        slug = f"{base_slug}-{counter}"

        counter += 1


@router.post(
    "",
    response_model=BlogResponse
)
def create_blog(
    blog_data: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    slug = unique_slug(
        blog_data.title,
        db
    )

    published_at = None

    if blog_data.status.lower() == "published":
        published_at = datetime.utcnow()

    blog = Blog(
        title=blog_data.title,
        slug=slug,
        excerpt=blog_data.excerpt,
        content=blog_data.content,
        featured_image=blog_data.featured_image,
        author=blog_data.author,
        category=blog_data.category,
       
        status=blog_data.status.lower(),
        published_at=published_at
    )

    db.add(blog)

    db.commit()

    db.refresh(blog)

    return blog


@router.get(
    "",
    response_model=list[BlogResponse]
)
def get_blogs(
    db: Session = Depends(get_db)
):
    """Public listing for the website - published posts only, newest first."""
    return (
        db.query(Blog)
        .filter(Blog.status == "published")
        .order_by(Blog.published_at.desc().nullslast(), Blog.created_at.desc())
        .all()
    )


@router.get(
    "/manage",
    response_model=list[BlogResponse]
)
def get_all_blogs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin listing - drafts and published."""
    return (
        db.query(Blog)
        .order_by(Blog.created_at.desc())
        .all()
    )


@router.get(
    "/slug/{slug}",
    response_model=BlogResponse
)
def get_blog_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    blog = (
        db.query(Blog)
        .filter(Blog.slug == slug, Blog.status == "published")
        .first()
    )

    if blog is None:
        raise HTTPException(
            status_code=404,
            detail="Blog post not found"
        )

    return blog


@router.delete(
    "/{blog_id}",
    status_code=204
)
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    blog = (
        db.query(Blog)
        .filter(Blog.id == blog_id)
        .first()
    )

    if blog is None:
        raise HTTPException(
            status_code=404,
            detail="Blog post not found"
        )

    db.delete(blog)
    db.commit()
