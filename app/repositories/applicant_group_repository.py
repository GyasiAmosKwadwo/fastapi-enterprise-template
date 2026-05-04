from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Applicant, ApplicantGroup
from app.models.associations import group_applicants


class ApplicantGroupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> ApplicantGroup:
        group = ApplicantGroup(**data)
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def get_by_id_and_client(self, group_id, client_id) -> Optional[ApplicantGroup]:
        result = await self.db.execute(
            select(ApplicantGroup).where(
                ApplicantGroup.id == group_id, ApplicantGroup.client_id == client_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_client(self, client_id: str) -> List[ApplicantGroup]:
        result = await self.db.execute(
            select(ApplicantGroup).where(ApplicantGroup.client_id == client_id)
        )
        return list(result.scalars().all())

    async def add_applicant_to_group(self, group_id, applicant_id):
        from sqlalchemy.dialects.postgresql import insert

        stmt = (
            insert(group_applicants)
            .values(group_id=group_id, applicant_id=applicant_id)
            .on_conflict_do_nothing()
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def remove_applicant_from_group(self, group_id, applicant_id):
        stmt = delete(group_applicants).where(
            group_applicants.c.group_id == group_id, group_applicants.c.applicant_id == applicant_id
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def list_applicants_in_group(self, group_id) -> List[Applicant]:
        result = await self.db.execute(
            select(Applicant)
            .join(group_applicants, Applicant.id == group_applicants.c.applicant_id)
            .where(group_applicants.c.group_id == group_id)
        )
        return list(result.scalars().all())

    async def delete(self, group_id):
        group = await self.db.get(ApplicantGroup, group_id)
        if group:
            await self.db.delete(group)
            await self.db.commit()
            return True
        return False
