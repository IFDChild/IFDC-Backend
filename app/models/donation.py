from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class DonationInterest(Base):
    """Someone who said they are willing to donate - followed up by email."""

    __tablename__ = "donation_interests"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(255), nullable=False, index=True)

    name = Column(String(255), nullable=True)

    # new -> contacted -> closed
    status = Column(String(50), nullable=False, default="new")

    notes = Column(Text, nullable=True)

    # Whether the admin notification email was sent successfully.
    admin_notified = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
