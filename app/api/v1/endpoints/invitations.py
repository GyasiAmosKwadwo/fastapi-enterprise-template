import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_redis
from app.core.permissions import require_permission
from app.models.invitation import Invitation, InvitationStatus
from app.models.user import User
from app.schemas.invitation import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
    PaginatedInvitationResponse,
)
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    data: InvitationCreate,
    current_user: User = Depends(require_permission("user.invite")),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Invite team member or client
    - Team invitations: Invite internal staff with admin roles
    - Client invitations: Onboard new client companies
    """
    invitation_service = InvitationService(db, redis)
    invitation = await invitation_service.create_invitation(data, current_user.id)
    return invitation


@router.post("/accept", status_code=status.HTTP_201_CREATED)
async def accept_invitation(
    data: InvitationAccept, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    """Accept invitation and create account"""
    invitation_service = InvitationService(db, redis)
    result = await invitation_service.accept_invitation(data)
    return result


@router.get("", response_model=PaginatedInvitationResponse)
async def list_invitations(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[InvitationStatus] = Query(None, description="Filter by status"),
    invitation_type: Optional[str] = Query(None, description="Filter by type: team or client"),
    search: Optional[str] = Query(None, description="Search by email or company name"),
    current_user: User = Depends(require_permission("user.invite")),
    db: AsyncSession = Depends(get_db),
):
    """
    List all invitations with pagination and filters
    """
    # Build query
    query = select(Invitation).order_by(Invitation.created_at.desc())

    # Apply filters
    filters = []

    if status:
        filters.append(Invitation.status == status)

    if invitation_type:
        if invitation_type not in ["team", "client"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invitation_type must be 'team' or 'client'",
            )
        filters.append(Invitation.invitation_type == invitation_type)

    if search:
        search_filter = or_(
            Invitation.email.ilike(f"%{search}%"), Invitation.company_name.ilike(f"%{search}%")
        )
        filters.append(search_filter)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(Invitation)
    if filters:
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    invitations = result.scalars().all()

    # Calculate pagination metadata
    total_pages = (total + per_page - 1) // per_page

    return {
        "data": invitations,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


@router.get("/{invitation_id}", response_model=InvitationResponse)
async def get_invitation(
    invitation_id: uuid.UUID,
    current_user: User = Depends(require_permission("user.invite")),
    db: AsyncSession = Depends(get_db),
):
    """Get invitation details"""
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    return invitation


@router.post("/{invitation_id}/resend")
async def resend_invitation(
    invitation_id: uuid.UUID,
    current_user: User = Depends(require_permission("user.invite")),
    db: AsyncSession = Depends(get_db),
):
    """Resend invitation email"""
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Can only resend pending invitations"
        )

    # Get role and inviter details
    from app.repositories.role_repository import RoleRepository
    from app.repositories.user_repository import UserRepository
    from app.services.email_service import EmailService

    role_repo = RoleRepository(db)
    user_repo = UserRepository(db)
    email_service = EmailService()

    role = await role_repo.get_by_id(invitation.role_id)
    inviter = await user_repo.get_by_id(invitation.invited_by_id)
    inviter_name = f"{inviter.first_name} {inviter.last_name}"

    # Resend email
    if invitation.invitation_type == "team":
        email_service.send_team_invitation_email(
            to_email=invitation.email,
            inviter_name=inviter_name,
            role_name=role.name,
            invitation_token=invitation.token,
            message=invitation.message,
        )
    else:  # client
        email_service.send_client_invitation_email(
            to_email=invitation.email,
            inviter_name=inviter_name,
            company_name=invitation.company_name,
            invitation_token=invitation.token,
            message=invitation.message,
        )

    return {"message": "Invitation resent successfully"}


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    invitation_id: uuid.UUID,
    current_user: User = Depends(require_permission("user.invite")),
    db: AsyncSession = Depends(get_db),
):
    """Cancel pending invitation"""
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Can only cancel pending invitations"
        )

    invitation.status = InvitationStatus.CANCELLED
    await db.commit()
