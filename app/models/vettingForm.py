# import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from app.core.database import Base


class VettingForm(Base):
    __tablename__ = "vetting_forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    personal_details = relationship("PersonalDetails", uselist=False, back_populates="vetting_form")
    marital_status = relationship("MaritalStatus", uselist=False, back_populates="vetting_form")
    education_bg = relationship(
        "EducationalBg", back_populates="vetting_form", cascade="all, delete-orphan"
    )
    employment_history = relationship(
        "EmploymentHistory", back_populates="vetting_form", cascade="all, delete-orphan"
    )

    applicant = relationship("Applicant", back_populates="vetting_form")


class PersonalDetails(Base):
    __tablename__ = "personal_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vetting_form_id = Column(UUID(as_uuid=True), ForeignKey("vetting_forms.id", ondelete="CASCADE"))
    first_name = Column(String(50))
    other_names = Column(String(50))
    surname = Column(String(50))
    previous_names = Column(String(50))
    passport_picture = Column(String(255))
    current_position = Column(String(100))
    employee_id = Column(String(100))
    department = Column(String(100))
    dob = Column(DateTime)
    pob = Column(String(100))
    nationality = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    current_res_add = Column(MutableDict.as_mutable(JSON))
    permanent_res_add = Column(MutableDict.as_mutable(JSON))
    mothers_full_name = Column(String(100))
    fathers_full_name = Column(String(100))
    national_id = Column(String(100))
    ssn = Column(String(100))
    ghana_card_no = Column(String(100))

    vetting_form = relationship("VettingForm", back_populates="personal_details")


class MaritalStatus(Base):
    """Marital Status store in database"""

    __tablename__ = "marital_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vetting_form_id = Column(UUID(as_uuid=True), ForeignKey("vetting_forms.id", ondelete="CASCADE"))
    status = Column(String(50))  # e.g., Single, Married, Divorced
    spouse_name = Column(String(100))
    spouse_occupation = Column(String(100))

    vetting_form = relationship("VettingForm", back_populates="marital_status")


class EducationalBg(Base):
    __tablename__ = "educational_bg"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vetting_form_id = Column(UUID(as_uuid=True), ForeignKey("vetting_forms.id", ondelete="CASCADE"))
    institution = Column(String(255))
    qualification = Column(String(255))
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    vetting_form = relationship("VettingForm", back_populates="education_bg")


class EmploymentHistory(Base):
    __tablename__ = "employment_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vetting_form_id = Column(UUID(as_uuid=True), ForeignKey("vetting_forms.id", ondelete="CASCADE"))
    employer_name = Column(String(255))
    position = Column(String(100))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    reason_for_leaving = Column(String(255))

    vetting_form = relationship("VettingForm", back_populates="employment_history")
