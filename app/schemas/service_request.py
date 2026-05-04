import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

# Allowed nationalities (can be expanded or fetched dynamically)
ALLOWED_NATIONALITIES = [
    "Ghanaian",
    "Nigerian",
    "Kenyan",
    "South African",
    "Ivorian",
    "Togolese",
    "Burkinabe",
    "American",
    "British",
    "Canadian",
]


class ServiceTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    cost: Decimal = Field(..., gt=0)


class ServiceTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cost: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ServiceTypeResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    cost: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceRequestCreate(BaseModel):
    service_type_id: uuid.UUID
    applicant_ids: Optional[List[uuid.UUID]] = None
    applicant_group_ids: Optional[List[uuid.UUID]] = None
    notes: Optional[str] = None
    expires_in_days: int = Field(default=7, ge=1, le=30)  # Expiry for form submission
    client_id: Optional[uuid.UUID] = None  # Allow admin to specify client_id


class ServiceRequestUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class AddressSchema(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class PersonalDetailsSchema(BaseModel):
    first_name: Optional[str]
    other_names: Optional[str]
    surname: Optional[str]
    previous_names: Optional[str]
    passport_picture: Optional[str]
    current_position: Optional[str]
    employee_id: Optional[str]
    department: Optional[str]
    dob: Optional[date]
    pob: Optional[str]
    nationality: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    current_res_add: Optional[AddressSchema]
    permanent_res_add: Optional[AddressSchema]
    mothers_full_name: Optional[str]
    fathers_full_name: Optional[str]
    national_id: Optional[str]
    ssn: Optional[str]
    ghana_card_no: Optional[str]

    # ───── Validators ─────

    @validator("ghana_card_no")
    def validate_ghana_card(cls, v):
        pattern = r"^GHA-\d{9}-\d$"
        if not re.match(pattern, v):
            raise ValueError("Invalid Ghana Card number format. Expected: GHA-XXXXXXXXX-X")
        return v

    @validator("phone")
    def validate_phone(cls, v):
        if v is None:
            return v
        # Ghana phone number pattern: +233XXXXXXXXX or 0XXXXXXXXX
        pattern = r"^(?:\+233|0)[2-9]\d{8}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid Ghanaian phone number format")
        return v

    @validator("employee_id")
    def validate_employee_id(cls, v):
        if v is None:
            return v
        if not re.match(r"^[A-Za-z0-9\-]+$", v):
            raise ValueError("Employee ID must be alphanumeric")
        return v

    @validator("nationality")
    def validate_nationality(cls, v):
        if v is None:
            return v
        if v not in ALLOWED_NATIONALITIES:
            raise ValueError(
                f"Invalid nationality. Must be one of: {', '.join(ALLOWED_NATIONALITIES)}"
            )
        return v


class MaritalStatusSchema(BaseModel):
    status: Optional[str]  # e.g., Single, Married, Divorced
    spouse_name: Optional[str]
    spouse_occupation: Optional[str]


class EducationalBgSchema(BaseModel):
    institution: Optional[str]
    qualification: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]


class EmploymentHistorySchema(BaseModel):
    employer_name: Optional[str]
    position: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    reason_for_leaving: Optional[str]


# ─────────────────────────────
# Main Vetting Form
# ─────────────────────────────


class VettingFormSubmit(BaseModel):
    personal_details: Optional[PersonalDetailsSchema] = None
    marital_status: Optional[MaritalStatusSchema] = None
    education_bg: Optional[List[EducationalBgSchema]] = None
    employment_history: Optional[List[EmploymentHistorySchema]] = None
    consent_accepted: bool = Field(..., description="Must be true to submit")
    applicant_id: uuid.UUID

    # ───── Validators ─────

    @validator("consent_accepted")
    def validate_consent(cls, v):
        if not v:
            raise ValueError("Consent must be accepted to submit form")
        return v


class ServiceRequestResponse(BaseModel):
    id: uuid.UUID
    reference_number: str
    client_id: uuid.UUID
    service_type_id: uuid.UUID
    status: str
    consent_status: str
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportSectionCreate(BaseModel):
    name: str
    content: str
    results_advisory: Optional[str] = None
    images: List[str] = []
    order: int = 0


class ReportCreate(BaseModel):
    service_request_id: uuid.UUID
    applicant_id: uuid.UUID
    executive_summary: str
    sections: List[ReportSectionCreate]


class SectionChallengeCreate(BaseModel):
    section_id: uuid.UUID
    reason: str
    supporting_docs: List[str] = []


class SectionChallengeResponse(BaseModel):
    id: uuid.UUID
    section_id: uuid.UUID
    applicant_id: uuid.UUID
    reason: str
    supporting_docs: List[str]
    status: str
    admin_response: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
