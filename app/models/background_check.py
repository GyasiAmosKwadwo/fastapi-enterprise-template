import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CheckType(str, enum.Enum):
    CRIMINAL = "criminal"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    FINANCIAL = "financial"
    IDENTITY = "identity"
    ADDRESS = "address"
    REFERENCE = "reference"


class CheckStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CheckResult(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NON_SATISFACTORY = "non_satisfactory"
    PENDING = "pending"


class BackgroundCheck(Base):
    __tablename__ = "background_checks"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )

    check_type = Column(Enum(CheckType), nullable=False)
    status = Column(Enum(CheckStatus), default=CheckStatus.PENDING)
    result = Column(Enum(CheckResult), nullable=True)

    # Check Data
    request_data = Column(JSON)  # Data sent to external API
    response_data = Column(JSON)  # Response from external API
    findings = Column(Text)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applicant = relationship("Applicant")
