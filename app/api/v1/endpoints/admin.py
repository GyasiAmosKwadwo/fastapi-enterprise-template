import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_permission
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserRoleUpdate, UsersListResponse, UserStatusUpdate, ClientResponse, StaffResponse, ClientsListResponse, StaffListResponse
from app.models.user import User
from app.models.user import UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])

#update user status
@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserStatusUpdate,
    current_user: User = Depends(require_permission("user.update")),
    db: AsyncSession = Depends(get_db),
):
    """Update user"""
    user_repo = UserRepository(db)

    update_data = data.dict(exclude_unset=True)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    elif user.role == UserRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update super admin role"
        )

    else:
        await user_repo.update(user_id, update_data)
        return user


# Update User Role
@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    current_user: User = Depends(require_permission("user.update")),
    db: AsyncSession = Depends(get_db),
):
    """Update user"""
    user_repo = UserRepository(db)

    update_data = data.dict(exclude_unset=True)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    elif user.role == UserRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update super admin role"
        )

    else:
        await user_repo.update(user_id, update_data)
        return user
    



@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permission("audit.view")),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs"""
    from sqlalchemy import select

    from app.models.audit import AuditLog

    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    )
    logs = result.scalars().all()
    return logs


"""
Admin dashboard analytics 
"""

@router.get("/users", response_model=UsersListResponse)
async def get_all_users(
    per_page: int = 20,
    name: Optional[str] = Query(None, description="Filter users by name"),
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
    role: Optional[UserRole] = Query(None, description="Filter users by role"),
    is_active: Optional[bool] = Query(None, description="Filter users by active status"),
    last_login: Optional[datetime] = Query(None, description="Filter users by last login"),
    phone_number: Optional[str] = Query(None, description="Filter users by phone number"),
    email: Optional[str] = Query(None, description="Filter users by email"),
    page: int = 1
     
):
    """List all users with pagination metadata"""
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20

    skip = (page - 1) * per_page

    user_repo = UserRepository(db)
    filters = {}
    if role is not None:
        filters["role"] = role
    if is_active is not None:
        filters["is_active"] = is_active
    if last_login is not None:
        filters["last_login"] = last_login
    if name is not None:
        filters["name"] = name
    if phone_number is not None:
        filters["phone_number"] = phone_number
    if email is not None:
        filters["email"] = email
     

    items = await user_repo.get_all(skip, per_page, filters=filters if filters else None)
    total_users = await user_repo.count(filters=filters if filters else None)

    total_pages = (total_users + per_page - 1) // per_page if per_page else 0
    has_next = page < total_pages
    has_prev = page > 1 and total_pages > 0

    return {
        "items": items,
        "pagination": {
            "total": total_users,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        },
    }


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID,
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
):
    """Get user details"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

@router.get("/staff", response_model=StaffListResponse)
async def get_all_staff(
    per_page: int = 20,
    name: Optional[str] = Query(None, description="Filter staff by name"),
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
    is_active: Optional[bool] = Query(None, description="Filter staff by active status"),
    last_login: Optional[datetime] = Query(None, description="Filter staff by last login"),
    phone_number: Optional[str] = Query(None, description="Filter staff by phone number"),
    email: Optional[str] = Query(None, description="Filter users by email"),
    page: int = 1
    ):
    """List all staff with pagination metadata"""
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    
    skip = (page - 1) * per_page

    user_repo = UserRepository(db)
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if last_login is not None:
        filters["last_login"] = last_login
    if name is not None:
        filters["name"] = name
    if phone_number is not None:
        filters["phone_number"] = phone_number
    if email is not None:
        filters["email"] = email
    
    items = await user_repo.get_all_staff(skip, per_page, filters=filters if filters else None)
    total_staff = await user_repo.count_staff(filters=filters if filters else None)
    
    total_pages = (total_staff + per_page - 1) // per_page if per_page else 0
    has_next = page < total_pages
    has_prev = page > 1 and total_pages > 0
    
    return {
        "items": items,
        "pagination": {
            "total": total_staff,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        },
    }

@router.get("/staff/{user_id}", response_model=StaffResponse)
async def get_staff(user_id: uuid.UUID,
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
):
    """Get staff details"""
    user_repo = UserRepository(db)
    user = await user_repo.get_staff_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

@router.get("/clients", response_model=ClientsListResponse)
async def get_all_clients(
    per_page: int = 20,
    corporate_name: Optional[str] = Query(None, description="Filter clients by name"),
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
    is_active: Optional[bool] = Query(None, description="Filter clients by active status"),
    last_login: Optional[datetime] = Query(None, description="Filter clients by last login"),
    corporate_phone_number: Optional[str] = Query(None, description="Filter clients by company phone number"),corporate_email: Optional[str] = Query(None, description="Filter clients by corporate email"),
    corporate_address: Optional[str] = Query(None, description="Filter clients by corporate address"),
    page: int = 1
):
    # Normalize pagination and compute skip
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20

    skip = (page - 1) * per_page

    user_repo = UserRepository(db)
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if last_login is not None:
        filters["last_login"] = last_login
    if corporate_name is not None:
        filters["corporate_name"] = corporate_name
    if corporate_phone_number is not None:
        filters["corporate_phone_number"] = corporate_phone_number
    if corporate_email is not None:
        filters["corporate_email"] = corporate_email
    if corporate_address is not None:
        filters["corporate_address"] = corporate_address
    
    items = await user_repo.get_all_clients(skip, per_page, filters=filters if filters else None)
    total_clients = await user_repo.count_clients(filters=filters if filters else None)
    
    for client in items:
        client.number_of_applicants = await user_repo.get_number_of_applicants(client.id)

    
    
    total_pages = (total_clients + per_page - 1) // per_page if per_page else 0
    has_next = page < total_pages
    has_prev = page > 1 and total_pages > 0
    
    return {
        "items": items,
        "pagination": {
            "total": total_clients,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        },
    }

@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    client = await user_repo.get_client_by_id(client_id)

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    client.number_of_applicants = await user_repo.get_number_of_applicants(client.id)
    return client

"""
@router.get("/agencies", response_model=AgencyResponse)
async def get_all_agencies(
    per_page: int = 20,
    name: Optional[str] = Query(None, description="Filter agencies by name"),
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),
    is_active: Optional[bool] = Query(None, description="Filter agencies by active status"),
    last_login: Optional[datetime] = Query(None, description="Filter agencies by last login"),
    agency_type: Optional[str] = Query(None, description="Filter agencies by agency type"),
    official_domain: Optional[str] = Query(None, description="Filter agents by official domain"),
    address: Optional[str] = Query(None, description="Filter agents by address"),
    page: int = 1
):
    user_repo = UserRepository(db)
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if last_login is not None:
        filters["last_login"] = last_login
    if agency_type is not None:
        filters["agency_type"] = agency_type
    if official_domain is not None:
        filters["official_domain"] = official_domain
    if address is not None:
        filters["address"] = address
    if name is not None:
        filters["name"] = name
    
    items = await user_repo.get_all_agents(skip, per_page, filters=filters if filters else None)
    total_agents = await user_repo.count(filters=filters if filters else None)
    
    total_pages = (total_agents + per_page - 1) // per_page if per_page else 0
    has_next = page < total_pages
    has_prev = page > 1 and total_pages > 0
    
    return {
        "items": items,
        "pagination": {
            "total": total_agents,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        },
    }

@router.get("/agency/{agency_id}", response_model=AgencyResponse)
async def get_agency(
    agency_id: uuid.UUID,
    current_user: User = Depends(require_permission("user.view")),
    db: AsyncSession = Depends(get_db),  
):
    user_repo = UserRepository(db)
    user = await user_repo.get_agency_by_id(agency_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    return user

"""

    




