import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_client, get_current_user, get_db
from app.models.service_request import ServiceRequest
from app.models.user import User, UserRole
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestResponse,
    ServiceRequestUpdate,
    VettingFormSubmit,
)
from app.services.service_request_service import ServiceRequestService

router = APIRouter(prefix="/service-requests", tags=["Service Requests"])


@router.post("", response_model=ServiceRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_service_request(
    data: ServiceRequestCreate,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Create service request (Client only)"""
    service_request_service = ServiceRequestService(db)

    target_client_id: uuid.UUID

    if current_user.role == UserRole.CLIENT:
        if not current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client user is not associated with a client ID.",
            )
        target_client_id = current_user.client_id
    elif current_user.role == UserRole.ADMINISTRATOR:
        if not data.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin users must specify a client_id in the request body.",
            )
        target_client_id = data.client_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role not authorized to create service requests.",
        )

    service_request = await service_request_service.create_service_request(
        data,
        target_client_id,
        current_user.id,  # created_by_id is the user who initiated the request
    )

    return service_request


@router.get("", response_model=List[ServiceRequestResponse])
async def list_service_requests(
    status_filter: str = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List service requests based on user role"""
    query = select(ServiceRequest)
    # Filter based on role
    if current_user.role == "client":
        query = query.where(ServiceRequest.client_id == current_user.client_id)
    elif current_user.role == "applicant":
        # Show requests where user is an applicant
        from app.models.service_request import service_request_applicants

        query = query.join(service_request_applicants).where(
            service_request_applicants.c.applicant_id == current_user.id
        )
    # Admins see all

    if status_filter:
        query = query.where(ServiceRequest.status == status_filter)

    query = query.order_by(ServiceRequest.created_at.desc())
    result = await db.execute(query)

    return result.scalars().all()


@router.get("/{service_request_id}", response_model=ServiceRequestResponse)
async def get_service_request(
    service_request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get service request details"""
    service_request = await db.get(ServiceRequest, service_request_id)

    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found"
        )

    # Check authorization
    if current_user.role == "client":
        if str(service_request.client_id) != str(current_user.client_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return service_request


@router.post("/{service_request_id}/submit-form")
async def submit_vetting_form(
    service_request_id: uuid.UUID,
    data: VettingFormSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Submit vetting form (Public endpoint with service request ID)"""
    # This endpoint doesn't require authentication
    # Applicant accesses via email link

    service_request_service = ServiceRequestService(db)

    # Get applicant ID from form data or query param
    # For now, we'll need to pass applicant_id in request
    applicant_id = data.applicant_id

    if not applicant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Applicant ID required")

    ip_address = request.client.host

    service_request = await service_request_service.submit_vetting_form(
        service_request_id, applicant_id, data, ip_address
    )

    return {
        "message": "Vetting form submitted successfully",
        "reference_number": service_request.reference_number,
    }


@router.post("/{service_request_id}/forward")
async def forward_to_admin(
    service_request_id: str,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Forward service request to admin for background check"""
    service_request_service = ServiceRequestService(db)

    service_request = await service_request_service.forward_to_admin(
        service_request_id, str(current_user.client_id), current_user.id
    )

    return {
        "message": "Service request forwarded to admin successfully",
        "reference_number": service_request.reference_number,
    }


@router.patch("/{service_request_id}", response_model=ServiceRequestResponse)
async def update_service_request(
    service_request_id: str,
    data: ServiceRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update service request"""
    service_request = await db.get(ServiceRequest, service_request_id)

    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found"
        )

    # Check authorization
    if current_user.role == "client":
        if str(service_request.client_id) != str(current_user.client_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service_request, field, value)

    await db.commit()
    await db.refresh(service_request)

    return service_request
