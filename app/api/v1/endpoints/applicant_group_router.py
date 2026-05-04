from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_client, get_db
from app.schemas.applicant import ApplicantResponse
from app.schemas.applicant_group import ApplicantGroupCreate, ApplicantGroupResponse
from app.services.applicant_group_service import ApplicantGroupService

router = APIRouter(prefix="/applicant-groups", tags=["Applicant Groups"])


@router.post("", response_model=ApplicantGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: ApplicantGroupCreate,
    db: AsyncSession = Depends(get_db),
    client=Depends(get_current_client),
):
    service = ApplicantGroupService(db)
    return await service.create_group(data, client.client_id)


@router.get("", response_model=List[ApplicantGroupResponse])
async def list_groups(db: AsyncSession = Depends(get_db), client=Depends(get_current_client)):
    service = ApplicantGroupService(db)
    return await service.list_groups(client.client_id)


@router.post("/{group_id}/applicants/{applicant_id}")
async def add_applicant(
    group_id: str,
    applicant_id: str,
    db: AsyncSession = Depends(get_db),
    client=Depends(get_current_client),  # This client is a User object
):
    service = ApplicantGroupService(db)
    return await service.add_applicant_to_group(group_id, applicant_id, client.client_id)


@router.delete("/{group_id}/applicants/{applicant_id}")
async def remove_applicant(
    group_id: str,
    applicant_id: str,
    db: AsyncSession = Depends(get_db),
    client=Depends(get_current_client),  # This client is a User object
):
    service = ApplicantGroupService(db)
    return await service.remove_applicant_from_group(group_id, applicant_id, client.client_id)


@router.get("/{group_id}/applicants", response_model=List[ApplicantResponse])
async def list_group_applicants(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    client=Depends(get_current_client),  # This client is a User object
):
    service = ApplicantGroupService(db)
    return await service.list_applicants_in_group(group_id, client.client_id)


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    client=Depends(get_current_client),  # This client is a User object
):
    service = ApplicantGroupService(db)
    return await service.delete_group(group_id, client.client_id)
