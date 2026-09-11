from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class PartnerInquiry(Base):

    __tablename__ = "partner_inquiries"

    id = Column(Integer, primary_key=True, index=True)

    organization_name = Column(String(255), nullable=False)

    contact_person = Column(String(255), nullable=False)

    email = Column(
        String(255),
        nullable=False,
        index=True
    )

    website = Column(String(500))

    partnership_type = Column(String(100), nullable=False)

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
