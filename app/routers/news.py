import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.news import News
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.news import (
    NEWS_CATEGORIES,
    NewsCreate,
    NewsResponse,
    NewsUpdate,
)


router = APIRouter(
    prefix="/api/news",
    tags=["News"]
)


def _slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "news"


def _unique_slug(title: str, db: Session, news_id: Optional[int] = None) -> str:
    base = _slugify(title)
    slug = base
    counter = 1

    while True:
        query = db.query(News).filter(News.slug == slug)
        if news_id is not None:
            query = query.filter(News.id != news_id)
        if query.first() is None:
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def _get_or_404(news_id: int, db: Session) -> News:
    item = db.query(News).filter(News.id == news_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="News article not found")
    return item


@router.get("/categories")
def list_categories():
    return {"categories": NEWS_CATEGORIES}


@router.get("", response_model=list[NewsResponse])
def list_published_news(
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """Public listing for the website - published articles only, newest first."""
    query = db.query(News).filter(News.status == "published")
    if category:
        query = query.filter(News.category == category)
    return query.order_by(News.published_at.desc().nullslast(), News.created_at.desc()).all()


@router.get("/manage", response_model=list[NewsResponse])
def list_all_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin listing - drafts and published."""
    return db.query(News).order_by(News.created_at.desc()).all()


@router.get("/slug/{slug}", response_model=NewsResponse)
def get_news_by_slug(slug: str, db: Session = Depends(get_db)):
    item = (
        db.query(News)
        .filter(News.slug == slug, News.status == "published")
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="News article not found")
    return item


@router.get("/{news_id}", response_model=NewsResponse)
def get_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return _get_or_404(news_id, db)


@router.post("", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
def create_news(
    payload: NewsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = News(
        title=payload.title,
        slug=_unique_slug(payload.title, db),
        summary=payload.summary,
        content=payload.content,
        image=payload.image,
        category=payload.category,
        status=payload.status,
        published_at=datetime.utcnow() if payload.status == "published" else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{news_id}", response_model=NewsResponse)
def update_news(
    news_id: int,
    payload: NewsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = _get_or_404(news_id, db)
    changes = payload.model_dump(exclude_unset=True)

    if "title" in changes and changes["title"] != item.title:
        item.slug = _unique_slug(changes["title"], db, news_id=item.id)

    for field, value in changes.items():
        setattr(item, field, value)

    if changes.get("status") == "published" and item.published_at is None:
        item.published_at = datetime.utcnow()
    elif changes.get("status") == "draft":
        item.published_at = None

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = _get_or_404(news_id, db)
    db.delete(item)
    db.commit()
