import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    FINALIZED = "finalized"


class ReportVersion(Base):
    """Report versions for tracking changes"""

    __tablename__ = "report_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )

    number = Column(Integer, nullable=False)  # Version number (1, 2, 3, etc.)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    changes_summary = Column(Text)  # What changed in this version

    # Relationships
    report = relationship("Report", back_populates="versions")
    created_by = relationship("User")


class ReportSection(Base):
    """Sections within a report"""

    __tablename__ = "report_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )

    name = Column(
        String(100), nullable=False
    )  # e.g., "Criminal Records", "Employment Verification"
    content = Column(Text)  # Section content
    results_advisory = Column(Text)  # Results and recommendations
    images = Column(JSON)  # Array of image URLs/paths

    order = Column(Integer, default=0)  # For ordering sections

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    report = relationship("Report", back_populates="sections")
    challenges = relationship(
        "SectionChallenge", back_populates="section", cascade="all, delete-orphan"
    )


class SectionChallenge(Base):
    """Challenges raised by applicants on report sections"""

    __tablename__ = "section_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(
        UUID(as_uuid=True), ForeignKey("report_sections.id", ondelete="CASCADE"), nullable=False
    )
    applicant_id = Column(
        UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )

    reason = Column(Text, nullable=False)
    supporting_docs = Column(JSON)  # Array of document URLs/paths

    status = Column(String(50), default="pending")  # pending, under_review, resolved, rejected
    admin_response = Column(Text)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    section = relationship("ReportSection", back_populates="challenges")
    applicant = relationship("Applicant")
    resolved_by = relationship("User")


class Report(Base):
    """Background check report"""

    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_request_id = Column(
        UUID(as_uuid=True), ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False
    )
    applicant_id = Column(
        UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )

    executive_summary = Column(Text)
    current_version = Column(Integer, default=1)

    file_path = Column(String(500))  # Path to generated PDF

    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    service_request = relationship("ServiceRequest", back_populates="reports")
    applicant = relationship("Applicant")
    versions = relationship(
        "ReportVersion",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportVersion.number.desc()",
    )
    sections = relationship(
        "ReportSection",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportSection.order",
    )
