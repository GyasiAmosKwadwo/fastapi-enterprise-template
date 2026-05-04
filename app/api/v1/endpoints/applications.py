from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.schemas.applicant import (
    ApplicantCreate,
    ApplicantResponse,
    ApplicantUpdate,
    PaginatedApplicantResponse,
)
from app.services.applicant_service import ApplicantService

router = APIRouter(prefix="/applicants", tags=["Applicants"])


@router.post("", response_model=ApplicantResponse, status_code=status.HTTP_201_CREATED)
async def create_applicant(
    data: ApplicantCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ApplicantService(db)
    return await service.create_applicant(data, current_user)


@router.put("/{applicant_id}", response_model=ApplicantResponse)
async def update_applicant(
    applicant_id: str,
    data: ApplicantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ApplicantService(db)
    return await service.update_applicant(applicant_id, data, current_user)


@router.delete("/{applicant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_applicant(
    applicant_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    service = ApplicantService(db)
    await service.delete_applicant(applicant_id, current_user)


@router.get("/{applicant_id}", response_model=ApplicantResponse)
async def get_applicant(
    applicant_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    service = ApplicantService(db)
    return await service.get_applicant_by_id(applicant_id, current_user)


@router.get("", response_model=PaginatedApplicantResponse)
async def list_applicants(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by applicant name or email"),
):
    service = ApplicantService(db)
    return await service.get_all_applicants_by_client(current_user, page, per_page, search)
