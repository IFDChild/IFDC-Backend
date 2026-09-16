from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class ContactMessage(Base):

    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)

    email = Column(
        String(255),
        nullable=False,
        index=True
    )

    phone = Column(String(50))

    subject = Column(String(100), nullable=False)

    message = Column(Text, nullable=False)

    # Review workflow
    status = Column(
        String(50),
        nullable=False,
        default="new"
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
