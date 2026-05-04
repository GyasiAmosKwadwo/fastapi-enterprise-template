import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ValidationStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    submission_date = Column(DateTime, default=datetime.utcnow)
    validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.PENDING)
    client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    vetting_form_id = Column(
        UUID(as_uuid=True), ForeignKey("vetting_forms.id", ondelete="SET NULL")
    )

    vetting_form = relationship("VettingForm", back_populates="applicant")
    client = relationship("Client", back_populates="applicants")
    groups = relationship(
        "ApplicantGroup", secondary="group_applicants", back_populates="applicants"
    )


class ApplicantGroup(Base):
    __tablename__ = "applicant_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="applicant_groups")
    applicants = relationship("Applicant", secondary="group_applicants", back_populates="groups")
