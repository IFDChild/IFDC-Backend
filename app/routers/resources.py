from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resource import Resource
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.resource import (
    AUDIENCES,
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
)


router = APIRouter(
    prefix="/api/resources",
    tags=["Resources"]
)


def _get_or_404(resource_id: int, db: Session) -> Resource:

    resource = (
        db.query(Resource)
        .filter(Resource.id == resource_id)
        .first()
    )

    if resource is None:
        raise HTTPException(
            status_code=404,
            detail="Resource not found"
        )

    return resource


@router.get("/audiences")
def list_audiences():
    """The audiences the website groups the library by."""

    return {"audiences": AUDIENCES}


@router.get(
    "",
    response_model=list[ResourceResponse]
)
def list_resources(
    audience: Optional[str] = Query(default=None),
    include_drafts: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    """
    Public listing for the website - published only by default.
    The admin passes include_drafts=true to see everything.
    """

    query = db.query(Resource)

    if not include_drafts:
        query = query.filter(Resource.status == "published")

    if audience:
        query = query.filter(Resource.audience == audience)

    return (
        query
        .order_by(Resource.created_at.desc())
        .all()
    )


@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED
)
def create_resource(
    resource_data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    resource = Resource(
        title=resource_data.title,
        description=resource_data.description,
        audience=resource_data.audience,
        category=resource_data.category,
        file_url=resource_data.file_url,
        file_name=resource_data.file_name,
        file_size=resource_data.file_size,
        thumbnail_url=resource_data.thumbnail_url,
        status=resource_data.status,
        downloads=0
    )

    db.add(resource)

    db.commit()

    db.refresh(resource)

    return resource


@router.patch(
    "/{resource_id}",
    response_model=ResourceResponse
)
def update_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    resource = _get_or_404(resource_id, db)

    for field, value in resource_data.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)

    db.commit()

    db.refresh(resource)

    return resource


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    resource = _get_or_404(resource_id, db)

    db.delete(resource)

    db.commit()


@router.post(
    "/{resource_id}/download",
    response_model=ResourceResponse
)
def register_download(
    resource_id: int,
    db: Session = Depends(get_db)
):
    """Called by the website when a visitor downloads the file."""

    resource = _get_or_404(resource_id, db)

    resource.downloads = (resource.downloads or 0) + 1

    db.commit()

    db.refresh(resource)

    return resource
