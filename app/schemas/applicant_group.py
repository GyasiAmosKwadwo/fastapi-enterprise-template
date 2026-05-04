from datetime import datetime
from typing import List, Optional

from pydantic import UUID4, BaseModel


class ApplicantGroupBase(BaseModel):
    name: str


class ApplicantGroupCreate(ApplicantGroupBase):
    pass


class ApplicantGroupUpdate(BaseModel):
    name: Optional[str] = None


class ApplicantGroupResponse(ApplicantGroupBase):
    id: UUID4
    client_id: UUID4
    created_at: datetime

    class Config:
        orm_mode = True
