import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    company_name = Column(String(255), nullable=False, unique=True)
    company_registration_number = Column(String(100), unique=True)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    address = Column(Text)

    contact_person_name = Column(String(200))
    contact_person_email = Column(String(255))
    contact_person_phone = Column(String(20))

    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default="basic")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="client")
    applicants = relationship("Applicant", back_populates="client", cascade="all, delete-orphan")
    applicant_groups = relationship(
        "ApplicantGroup", back_populates="client", cascade="all, delete-orphan"
    )
