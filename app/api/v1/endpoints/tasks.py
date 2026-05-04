from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.permissions import require_permission
from app.models.task import TaskComment, TaskStatus
from app.models.user import User
from app.schemas.task import (
    TaskCommentCreate,
    TaskCommentResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(require_permission("task.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create new task"""
    task_service = TaskService(db)
    task = await task_service.create_task(data, current_user.id)
    return task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    assigned_to_me: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tasks"""
    task_service = TaskService(db)

    if assigned_to_me:
        tasks = await task_service.task_repo.get_by_assigned_to(current_user.id, status)
    else:
        # Admin can see all tasks
        if current_user.role == "administrator":
            filters = {"status": status} if status else None
            tasks = await task_service.task_repo.get_all(filters=filters)
        else:
            # Others see only their assigned tasks
            tasks = await task_service.task_repo.get_by_assigned_to(current_user.id, status)

    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get task details"""
    task_service = TaskService(db)
    task = await task_service.task_repo.get_by_id(task_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Check authorization
    if (
        current_user.role != "administrator"
        and task.assigned_to_id != current_user.id
        and task.created_by_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this task"
        )

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task"""
    task_service = TaskService(db)
    task = await task_service.update_task(task_id, data, current_user.id)
    return task


@router.post("/{task_id}/assign")
async def assign_task(
    task_id: int,
    assigned_to_id: int,
    current_user: User = Depends(require_permission("task.assign")),
    db: AsyncSession = Depends(get_db),
):
    """Assign task to user"""
    task_service = TaskService(db)
    task = await task_service.assign_task(task_id, assigned_to_id, current_user.id)
    return {"message": "Task assigned successfully", "task_id": task.id}


@router.post("/{task_id}/comments", response_model=TaskCommentResponse)
async def add_comment(
    task_id: int,
    data: TaskCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add comment to task"""
    # Verify task exists
    task_service = TaskService(db)
    task = await task_service.task_repo.get_by_id(task_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Create comment
    comment = TaskComment(
        task_id=task_id, user_id=current_user.id, content=data.content, attachments=data.attachments
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return comment


@router.get("/{task_id}/comments", response_model=List[TaskCommentResponse])
async def get_task_comments(
    task_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get task comments"""
    from sqlalchemy import select

    result = await db.execute(
        select(TaskComment)
        .where(TaskComment.task_id == task_id)
        .order_by(TaskComment.created_at.asc())
    )
    comments = result.scalars().all()
    return comments
