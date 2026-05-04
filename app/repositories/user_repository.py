from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.models.user import User
from app.repositories.base import BaseRepository
from app.models.user import UserRole
from app.models.role import Role
from app.models.associations import user_roles
from app.models.invitation import Invitation, InvitationStatus


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        result = await self.db.execute(select(User).where(User.phone_number == phone_number))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by id"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: any) -> None:
        """Update last login timestamp"""
        await self.update(
            user_id,
            {
                "last_login": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "failed_login_attempts": 0,
            },
        )

    async def increment_failed_attempts(self, user_id: any) -> None:
        """Increment failed login attempts"""
        user = await self.get_by_id(user_id)
        if user:
            await self.update(user_id, {"failed_login_attempts": user.failed_login_attempts + 1})

    async def lock_account(self, user_id: any, until: any) -> None:
        """Lock user account"""
        await self.update(user_id, {"locked_until": until})

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users"""
        result = await self.db.execute(select(User).offset(skip).limit(limit))

        total_number = result.count()
        return result.scalars().all(), total_number

    async def get_all(self, skip: int = 0, limit: int = 100, filters: Optional[dict] = None) -> list[User]:
        """Get users with optional filters and pagination (used by /admin/users)"""
        query = select(User)

        if filters:
            if filters.get("role") is not None:
                # filters["role"] is likely a UserRole enum; compare to DB enum value
                role_value = getattr(filters["role"], "value", filters["role"])
                query = query.where(User.role == role_value)
            if filters.get("is_active") is not None:
                query = query.where(User.is_active == filters["is_active"])
            if filters.get("last_login") is not None:
                query = query.where(User.last_login >= filters["last_login"])  # simple lower bound
            if filters.get("phone_number") is not None:
                query = query.where(User.phone_number == filters["phone_number"])
            if filters.get("email") is not None:
                query = query.where(User.email == filters["email"])
            if filters.get("name") is not None:
                name = f"%{filters['name']}%"
                query = query.where(or_(User.first_name.ilike(name), User.last_name.ilike(name)))

        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def count(self, filters: Optional[dict] = None) -> int:
        """Count users matching optional filters (used by /admin/users)"""
        query = select(func.count()).select_from(User)

        if filters:
            if filters.get("role") is not None:
                role_value = getattr(filters["role"], "value", filters["role"])
                query = query.where(User.role == role_value)
            if filters.get("is_active") is not None:
                query = query.where(User.is_active == filters["is_active"])
            if filters.get("last_login") is not None:
                query = query.where(User.last_login >= filters["last_login"])  # simple lower bound
            if filters.get("phone_number") is not None:
                query = query.where(User.phone_number == filters["phone_number"])
            if filters.get("email") is not None:
                query = query.where(User.email == filters["email"])
            if filters.get("name") is not None:
                name = f"%{filters['name']}%"
                query = query.where(or_(User.first_name.ilike(name), User.last_name.ilike(name)))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_all_staff(self, skip: int = 0, limit: int = 100, filters: Optional[dict] = None) -> list[User]:
        """Get users onboarded via invitations with invitation_type == 'team' (accepted), with optional filters and pagination"""
        query = (
            select(User)
            .join(Invitation, Invitation.email == User.email)
            .where(Invitation.invitation_type == "team")
            .where(Invitation.status == InvitationStatus.ACCEPTED)
        )

        if filters:
            if filters.get("is_active") is not None:
                query = query.where(User.is_active == filters["is_active"])
            if filters.get("last_login") is not None:
                query = query.where(User.last_login >= filters["last_login"])  # simple lower bound
            if filters.get("phone_number") is not None:
                query = query.where(User.phone_number == filters["phone_number"])
            if filters.get("email") is not None:
                query = query.where(User.email == filters["email"])
            if filters.get("name") is not None:
                name = f"%{filters['name']}%"
                query = query.where(or_(User.first_name.ilike(name), User.last_name.ilike(name)))

        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def count_staff(self, filters: Optional[dict] = None) -> int:
        """Count users onboarded via invitations with invitation_type == 'team' (accepted) matching optional filters"""
        query = (
            select(func.count())
            .select_from(User)
            .join(Invitation, Invitation.email == User.email)
            .where(Invitation.invitation_type == "team")
            .where(Invitation.status == InvitationStatus.ACCEPTED)
        )

        if filters:
            if filters.get("is_active") is not None:
                query = query.where(User.is_active == filters["is_active"])
            if filters.get("last_login") is not None:
                query = query.where(User.last_login >= filters["last_login"])  # simple lower bound
            if filters.get("phone_number") is not None:
                query = query.where(User.phone_number == filters["phone_number"])
            if filters.get("email") is not None:
                query = query.where(User.email == filters["email"])
            if filters.get("name") is not None:
                name = f"%{filters['name']}%"
                query = query.where(or_(User.first_name.ilike(name), User.last_name.ilike(name)))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_staff_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by id"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_number_of_applicants(self, user_id: uuid.UUID) -> Optional[int]:
        """Get number of applicants for a client"""
        result = await self.db.execute(select(func.count()).select_from(User).where(User.client_id == user_id))
        return result.scalar_one()

    async def get_all_clients(self, skip: int = 0, limit: int = 100, filters: Optional[dict] = None) -> list[User]:
        """Get client users with optional filters and pagination"""
        query = select(User).where(User.role == UserRole.CLIENT.value)

        if filters:
            if filters.get("is_active") is not None:
                query = query.where(User.is_active == filters["is_active"])
            if filters.get("last_login") is not None:
                query = query.where(User.last_login >= filters["last_login"])  # simple lower bound
            if filters.get("corporate_phone_number") is not None:
                # placeholder: if corporate fields live on a related model, this will need joins
                pass
            if filters.get("corporate_email") is not None:
                pass
            if filters.get("corporate_address") is not None:
                pass
            if filters.get("corporate_name") is not None:
                pass
            if filters.get("email") is not None:
                query = query.where(User.email == filters["email"])

        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def count_clients(self, filters: Optional[dict] = None) -> int:
        """Count client users matching optional filters"""
        query = select(func.count()).select_from(User).where(User.role == UserRole.CLIENT.value)

        if filters:
            if filters.get("is_active") is not None:
                query = query.where(User.is_active == filters["is_active"])
            if filters.get("last_login") is not None:
                query = query.where(User.last_login >= filters["last_login"])  # simple lower bound
            if filters.get("email") is not None:
                query = query.where(User.email == filters["email"])

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_client_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by id"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
"""
    async def get_all_agencies(self, skip: int = 0, limit: int = 100) -> list[User]:
        #Get all users with agency role
        result = await self.db.execute(select(User).where(User.role == UserRole.AGENCY).offset(skip).limit(limit))

        total_number = result.count()
        return result.scalars().all(), total_number

    async def get_agency_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        #Get user by id
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
"""

