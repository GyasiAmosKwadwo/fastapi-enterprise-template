from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus
from app.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    def __init__(self, db: AsyncSession):
        super().__init__(Application, db)

    async def get_by_reference(self, reference_number: str) -> Optional[Application]:
        """Get application by reference number"""
        result = await self.db.execute(
            select(Application)
            .where(Application.reference_number == reference_number)
            .options(selectinload(Application.documents), selectinload(Application.checks))
        )
        return result.scalar_one_or_none()

    async def get_by_client(
        self, client_id: int, skip: int = 0, limit: int = 100
    ) -> List[Application]:
        """Get applications for a client"""
        result = await self.db.execute(
            select(Application)
            .where(Application.client_id == client_id)
            .offset(skip)
            .limit(limit)
            .order_by(Application.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_applicant(self, applicant_id: int) -> List[Application]:
        """Get applications for an applicant"""
        result = await self.db.execute(
            select(Application)
            .where(Application.applicant_id == applicant_id)
            .order_by(Application.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(
        self, status: ApplicationStatus, skip: int = 0, limit: int = 100
    ) -> List[Application]:
        """Get applications by status"""
        result = await self.db.execute(
            select(Application)
            .where(Application.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Application.created_at.desc())
        )
        return list(result.scalars().all())
