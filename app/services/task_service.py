from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskActivity, TaskStatus
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.notification_service import NotificationService


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)
        self.notification_service = NotificationService(db)

    async def create_task(self, data: TaskCreate, created_by_id: int) -> Task:
        """Create new task"""
        # Verify assigned user exists and has permission
        if data.assigned_to_id:
            assigned_user = await self.user_repo.get_by_id(data.assigned_to_id)
            if not assigned_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found"
                )

            # TODO: Check if user has permission for task type

        # Create task
        task_data = data.dict()
        task_data["created_by_id"] = created_by_id

        task = await self.task_repo.create(task_data)

        # Create activity log
        activity = TaskActivity(
            task_id=task.id,
            user_id=created_by_id,
            action="task_created",
            details={"task_type": task.task_type, "priority": task.priority},
        )
        self.db.add(activity)

        # Send notification to assigned user
        if data.assigned_to_id:
            await self.notification_service.create_task_assigned_notification(
                task=task, assigned_to_id=data.assigned_to_id
            )

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def update_task(self, task_id: int, data: TaskUpdate, user_id: int) -> Task:
        """Update task"""
        task = await self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        # Track changes for activity log
        changes = {}
        update_data = data.dict(exclude_unset=True)

        for field, value in update_data.items():
            old_value = getattr(task, field)
            if old_value != value:
                changes[field] = {"old": str(old_value), "new": str(value)}

        # Update task
        if update_data:
            task = await self.task_repo.update(task_id, update_data)

        # Create activity log
        if changes:
            activity = TaskActivity(
                task_id=task_id,
                user_id=user_id,
                action="task_updated",
                details={"changes": changes},
            )
            self.db.add(activity)

        # Send notification if status changed
        if "status" in changes and task.assigned_to_id:
            if data.status == TaskStatus.COMPLETED:
                await self.notification_service.create_task_completed_notification(task=task)

        # Send notification if reassigned
        if "assigned_to_id" in changes and data.assigned_to_id:
            await self.notification_service.create_task_assigned_notification(
                task=task, assigned_to_id=data.assigned_to_id
            )

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def assign_task(self, task_id: int, assigned_to_id: int, assigner_id: int) -> Task:
        """Assign task to user"""
        task = await self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        # Verify assigned user exists
        assigned_user = await self.user_repo.get_by_id(assigned_to_id)
        if not assigned_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Update task
        task = await self.task_repo.update(
            task_id, {"assigned_to_id": assigned_to_id, "status": TaskStatus.IN_PROGRESS}
        )

        # Create activity log
        activity = TaskActivity(
            task_id=task_id,
            user_id=assigner_id,
            action="task_assigned",
            details={"assigned_to": assigned_user.email, "assigned_to_id": assigned_to_id},
        )
        self.db.add(activity)

        # Send notification
        await self.notification_service.create_task_assigned_notification(
            task=task, assigned_to_id=assigned_to_id
        )

        await self.db.commit()
        await self.db.refresh(task)

        return task
