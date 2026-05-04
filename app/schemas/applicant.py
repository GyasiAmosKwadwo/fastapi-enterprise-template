from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.application import ValidationStatus


# ------------------------------
# 🧱 Base Applicant Schema
# ------------------------------
class ApplicantBase(BaseModel):
    full_name: str
    email: EmailStr
    vetting_form_id: Optional[UUID] = None


# ------------------------------
# 🆕 Create Applicant
# ------------------------------
class ApplicantCreate(ApplicantBase):
    pass


# ------------------------------
# 📝 Update Applicant
# ------------------------------
class ApplicantUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    validation_status: Optional[ValidationStatus] = None
    vetting_form_id: Optional[UUID] = None


# ------------------------------
# 📤 Response Schema
# ------------------------------
class ApplicantResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    submission_date: datetime
    validation_status: ValidationStatus
    client_id: UUID
    vetting_form_id: Optional[UUID] = None

    class Config:
        orm_mode = True


# ------------------------------
# 📄 Pagination Schemas
# ------------------------------
class ApplicantPagination(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class PaginatedApplicantResponse(BaseModel):
    data: List[ApplicantResponse]
    pagination: ApplicantPagination
