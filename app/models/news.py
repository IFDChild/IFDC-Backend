from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base


class News(Base):

    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)

    slug = Column(String(255), unique=True, nullable=False)

    summary = Column(Text)

    content = Column(Text, nullable=False)

    image = Column(String(500))

    category = Column(String(100))

    status = Column(String(50), default="draft")

    published_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )