import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr

from app.models.invitation import InvitationStatus


class InvitationCreate(BaseModel):
    email: EmailStr
    role_id: uuid.UUID
    client_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None  # For client invitations
    message: Optional[str] = None
    invitation_type: str = "team"  # "team" or "client"


class InvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    status: InvitationStatus
    role_id: uuid.UUID
    client_id: Optional[uuid.UUID]
    invitation_type: str
    expires_at: datetime
    created_at: datetime
    invited_by_id: uuid.UUID

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedInvitationResponse(BaseModel):
    data: List[InvitationResponse]
    pagination: Pagination


class CompanyDetails(BaseModel):
    company_name: Optional[str] = None
    registration_number: Optional[str] = None
    company_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class InvitationAccept(BaseModel):
    token: str
    first_name: str
    last_name: str
    password: str
    phone_number: Optional[str] = None
    company_details: Optional[CompanyDetails] = None  # For client invitations


class InvitationListFilter(BaseModel):
    status: Optional[InvitationStatus] = None
    invitation_type: Optional[str] = None  # "team" or "client"
    search: Optional[str] = None  # Search by email
