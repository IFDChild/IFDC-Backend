from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class VolunteerApplication(Base):

    __tablename__ = "volunteer_applications"

    id = Column(Integer, primary_key=True, index=True)

    # Step 1 - Basics
    first_name = Column(String(255), nullable=False)

    last_name = Column(String(255), nullable=False)

    email = Column(
        String(255),
        nullable=False,
        index=True
    )

    phone = Column(String(50))

    address = Column(Text, nullable=False)

    # Step 2 - About You
    describes = Column(String(100), nullable=False)

    interests = Column(
        JSONB,
        nullable=False,
        default=list
    )

    social_media = Column(String(500))

    # Step 3 - Motivation
    motivation = Column(Text, nullable=False)

    cv_url = Column(String(500))

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
