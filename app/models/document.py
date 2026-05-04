import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentType(str, enum.Enum):
    ID_CARD = "id_card"
    CERTIFICATE = "certificate"
    REFERENCE_LETTER = "reference_letter"
    EMPLOYMENT_LETTER = "employment_letter"
    RESIDENCE_PHOTO = "residence_photo"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False
    )

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))

    document_type = Column(Enum(DocumentType), nullable=False)
    description = Column(String(500))

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    applicant = relationship("Applicant")
