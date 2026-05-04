from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Applicant
from app.repositories.base import BaseRepository


class ApplicantRepository(BaseRepository[Applicant]):
    def __init__(self, db: AsyncSession):
        super().__init__(Applicant, db)

    async def get_by_client(
        self, client_id: str, page: int, per_page: int, search: Optional[str] = None
    ) -> Tuple[List[Applicant], int]:
        query = select(Applicant).where(Applicant.client_id == client_id)
        count_query = (
            select(func.count()).select_from(Applicant).where(Applicant.client_id == client_id)
        )

        if search:
            search_filter = or_(
                Applicant.full_name.ilike(f"%{search}%"), Applicant.email.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        offset = (page - 1) * per_page
        query = query.order_by(Applicant.submission_date.desc()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        applicants = list(result.scalars().all())
        return applicants, total
