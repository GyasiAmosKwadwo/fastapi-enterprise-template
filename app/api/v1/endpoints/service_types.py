from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.service_request import ServiceType
from app.models.user import User
from app.schemas.service_request import ServiceTypeCreate, ServiceTypeResponse, ServiceTypeUpdate

router = APIRouter(prefix="/service-types", tags=["Service Types"])


@router.post("", response_model=ServiceTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_service_type(
    data: ServiceTypeCreate,
    current_user: User = Depends(require_permission("service_type.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create service type (Admin only)"""
    # Check if name exists
    from sqlalchemy import select

    result = await db.execute(select(ServiceType).where(ServiceType.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service type with this name already exists",
        )

    service_type = ServiceType(**data.dict(), created_by_id=current_user.id)

    db.add(service_type)
    await db.commit()
    await db.refresh(service_type)

    return service_type


@router.get("", response_model=List[ServiceTypeResponse])
async def list_service_types(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all service types"""
    from sqlalchemy import select

    query = select(ServiceType)
    if not include_inactive:
        query = query.where(ServiceType.is_active == True)

    query = query.order_by(ServiceType.name)
    result = await db.execute(query)

    return result.scalars().all()


@router.get("/{service_type_id}", response_model=ServiceTypeResponse)
async def get_service_type(
    service_type_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get service type details"""
    service_type = await db.get(ServiceType, service_type_id)

    if not service_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service type not found")

    return service_type


@router.patch("/{service_type_id}", response_model=ServiceTypeResponse)
async def update_service_type(
    service_type_id: str,
    data: ServiceTypeUpdate,
    current_user: User = Depends(require_permission("service_type.update")),
    db: AsyncSession = Depends(get_db),
):
    """Update service type (Admin only)"""
    service_type = await db.get(ServiceType, service_type_id)

    if not service_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service type not found")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service_type, field, value)

    await db.commit()
    await db.refresh(service_type)

    return service_type


@router.delete("/{service_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_type(
    service_type_id: str,
    current_user: User = Depends(require_permission("service_type.delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete service type (Admin only)"""
    service_type = await db.get(ServiceType, service_type_id)

    if not service_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service type not found")

    # Soft delete by marking as inactive
    service_type.is_active = False
    await db.commit()
