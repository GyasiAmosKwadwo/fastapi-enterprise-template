import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: str
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    task_metadata: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assigned_to_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    task_metadata: Optional[Dict[str, Any]] = None


class TaskCommentCreate(BaseModel):
    content: str
    attachments: Optional[List[str]] = None


class TaskCommentResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    created_by_id: int
    assigned_to_id: Optional[uuid.UUID]
    application_id: Optional[uuid.UUID]
    due_date: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
