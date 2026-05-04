import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)

    # Invitation details
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)

    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)

    # Metadata
    message = Column(String(500))
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    invitation_type = Column(String(20), default="team", nullable=False)  # "team" or "client"
    company_name = Column(String(255), nullable=True)  # For client invitations

    # Relationships
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    role = relationship("Role")
    client = relationship("Client")
