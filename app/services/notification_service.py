import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.task import Task
from app.repositories.notification_repository import NotificationRepository

# from app.models.application import Application
from app.schemas.notification import NotificationCreate


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_repo = NotificationRepository(db)

    async def create_notification(self, data: NotificationCreate) -> Notification:
        """Create notification"""
        notification_data = data.dict()
        notification = await self.notification_repo.create(notification_data)

        # TODO: Send real-time notification via WebSocket
        # TODO: Send email if priority is HIGH
        # TODO: Send SMS for urgent notifications

        return notification

    async def create_task_assigned_notification(
        self, task: Task, assigned_to_id: uuid.UUID
    ) -> None:
        """Notify user when task is assigned"""
        notification_data = NotificationCreate(
            user_id=assigned_to_id,
            type=NotificationType.TASK_ASSIGNED,
            priority=(
                NotificationPriority.HIGH
                if task.priority == "urgent"
                else NotificationPriority.MEDIUM
            ),
            title="New Task Assigned",
            message=f"You have been assigned task: {task.title}",
            resource_type="task",
            resource_id=task.id,
            action_url=f"/tasks/{task.id}",
            data={
                "task_id": task.id,
                "task_type": task.task_type,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            },
        )
        await self.create_notification(notification_data)

    async def create_task_completed_notification(self, task: Task) -> None:
        """Notify task creator when task is completed"""
        notification_data = NotificationCreate(
            user_id=task.created_by_id,
            type=NotificationType.TASK_COMPLETED,
            priority=NotificationPriority.MEDIUM,
            title="Task Completed",
            message=f"Task '{task.title}' has been completed by {task.assigned_to.first_name} {task.assigned_to.last_name}",
            resource_type="task",
            resource_id=task.id,
            action_url=f"/tasks/{task.id}",
            data={"task_id": task.id, "completed_by": task.assigned_to_id},
        )
        await self.create_notification(notification_data)

    async def get_user_notifications(
        self, user_id: uuid.UUID, unread_only: bool = False
    ) -> List[Notification]:
        """Get user notifications"""
        return await self.notification_repo.get_user_notifications(user_id, unread_only)

    async def mark_as_read(self, notification_ids: List[uuid.UUID]) -> None:
        """Mark notifications as read"""
        await self.notification_repo.mark_as_read(notification_ids)

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get unread notification count"""
        return await self.notification_repo.get_unread_count(user_id)
