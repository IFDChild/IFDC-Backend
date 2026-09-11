from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class Resource(Base):

    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)

    description = Column(Text)

    # Who the resource is for - the website groups the library by this.
    audience = Column(
        String(100),
        nullable=False,
        index=True
    )

    category = Column(String(100))

    # Uploaded file, e.g. /uploads/<uuid>.pdf
    file_url = Column(String(500), nullable=False)

    file_name = Column(String(255))

    file_size = Column(Integer)

    # Cover image rendered from page 1 of the PDF
    thumbnail_url = Column(String(500))

    status = Column(
        String(50),
        nullable=False,
        default="published",
        index=True
    )

    downloads = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
