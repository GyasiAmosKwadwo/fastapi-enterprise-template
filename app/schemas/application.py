import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.application import ApplicationStatus


class EmploymentRecord(BaseModel):
    company_name: str
    position: str
    start_date: date
    end_date: Optional[date]
    is_current: bool = False
    reference_name: Optional[str]
    reference_contact: Optional[str]


class EducationRecord(BaseModel):
    institution_name: str
    degree: str
    field_of_study: str
    start_date: date
    end_date: Optional[date]
    graduation_date: Optional[date]


class ApplicationCreate(BaseModel):
    date_of_birth: date
    ghana_card_number: str
    permanent_address: str
    current_address: str
    employment_history: List[EmploymentRecord] = []
    education_history: List[EducationRecord] = []
    client_instructions: Optional[str] = None


class ApplicationUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    permanent_address: Optional[str] = None
    current_address: Optional[str] = None
    employment_history: Optional[List[EmploymentRecord]] = None
    education_history: Optional[List[EducationRecord]] = None
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    reference_number: str
    applicant_id: uuid.UUID
    client_id: uuid.UUID
    status: ApplicationStatus
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationDetail(ApplicationResponse):
    date_of_birth: Optional[datetime]
    ghana_card_number: Optional[str]
    permanent_address: Optional[str]
    current_address: Optional[str]
    permanent_address_gps: Optional[Dict[str, Any]]
    current_address_gps: Optional[Dict[str, Any]]
    employment_history: Optional[List[Dict]]
    education_history: Optional[List[Dict]]
    notes: Optional[str]

    class Config:
        from_attributes = True
