import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ServiceRequestStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPLICANT = "pending_applicant"  # Waiting for applicant to fill form
    SUBMITTED = "submitted"  # Applicant submitted, waiting for client forward
    FORWARDED = "forwarded"  # Client forwarded to admin
    IN_PROGRESS = "in_progress"  # Admin processing
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConsentStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


# Association table for service request and applicants
service_request_applicants = Table(
    "service_request_applicants",
    Base.metadata,
    Column(
        "service_request_id",
        ForeignKey("service_requests.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("applicant_id", ForeignKey("applicants.id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)


class ServiceType(Base):
    """Service types that can be requested (created by admin only)"""

    __tablename__ = "service_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    cost = Column(Numeric(10, 2), nullable=False)  # Cost in currency

    is_active = Column(Boolean, default=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    created_by = relationship("User")
    service_requests = relationship("ServiceRequest", back_populates="service_type")


class ServiceRequest(Base):
    """Service request created by client for applicant(s)"""

    __tablename__ = "service_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_number = Column(String(50), unique=True, nullable=False, index=True)

    # Foreign Keys
    client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    service_type_id = Column(UUID(as_uuid=True), ForeignKey("service_types.id"), nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # Admin assigned

    # Request Details
    status = Column(Enum(ServiceRequestStatus), default=ServiceRequestStatus.DRAFT, nullable=False)
    notes = Column(Text)  # Client notes

    # Consent
    consent_status = Column(Enum(ConsentStatus), default=ConsentStatus.PENDING)
    consent_accepted_at = Column(DateTime(timezone=True), nullable=True)
    consent_ip_address = Column(String(45))

    # Vetting Form (submitted by applicant)
    vetting_form_data = Column(JSON)  # Stores the filled form data
    vetting_form_submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Timing
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Expiry for applicant to submit
    submitted_to_admin_at = Column(
        DateTime(timezone=True), nullable=True
    )  # When client forwarded to admin
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    client = relationship("Client")
    service_type = relationship("ServiceType", back_populates="service_requests")
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    applicants = relationship(
        "Applicant", secondary=service_request_applicants, backref="service_requests"
    )
    reports = relationship("Report", back_populates="service_request", cascade="all, delete-orphan")
    notifications = relationship(
        "ServiceRequestNotification", back_populates="service_request", cascade="all, delete-orphan"
    )


class ServiceRequestNotification(Base):
    """Track notifications sent for service requests"""

    __tablename__ = "service_request_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_request_id = Column(
        UUID(as_uuid=True), ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False
    )
    applicant_id = Column(
        UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )

    notification_type = Column(String(50), nullable=False)  # e.g., "form_invitation", "reminder"
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_read = Column(Boolean, default=False)

    # Relationships
    service_request = relationship("ServiceRequest", back_populates="notifications")
    applicant = relationship("Applicant")
