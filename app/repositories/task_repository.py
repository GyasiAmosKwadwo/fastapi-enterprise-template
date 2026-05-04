from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskStatus
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: AsyncSession):
        super().__init__(Task, db)

    async def get_by_assigned_to(
        self, user_id: int, status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """Get tasks assigned to user"""
        query = select(Task).where(Task.assigned_to_id == user_id)

        if status:
            query = query.where(Task.status == status)

        query = query.order_by(Task.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_application(self, application_id: int) -> List[Task]:
        """Get tasks for an application"""
        result = await self.db.execute(
            select(Task)
            .where(Task.application_id == application_id)
            .order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        result = await self.db.execute(
            select(Task)
            .where(Task.status == TaskStatus.PENDING)
            .order_by(Task.priority.desc(), Task.created_at.asc())
        )
        return list(result.scalars().all())
