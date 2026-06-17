from fastapi import APIRouter, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from constants import (
    TASK_PRIORITIES,
    current_active_user,
    
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User
from models.tasks import Task, TaskHistory

from database import get_db 
from datetime import datetime, date
from typing import Optional

from services.tasks_cache import (
    invalidate_task_stats,
)
from services.task_realtime import task_connection_manager

from services.auth.fastapi_manager import auth_backend, get_user_manager

router = APIRouter()


def add_task_history(
    session: AsyncSession,
    user_id: int,
    method: str,
    task_title: str,
    task_id: int | None = None,
):
    session.add(
        TaskHistory(
            method=method,
            task_id=task_id,
            task_title=task_title,
            user_id=user_id,
        )
    )


async def get_owned_task(
    task_id: int,
    user: User,
    session: AsyncSession,
) -> Task:
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user.id)
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return task



@router.post("/tasks", response_class=HTMLResponse)
async def create_task(
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    deadline: Optional[date] = Form(None),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")
    
    task_priority = priority if priority in TASK_PRIORITIES else "medium"

    task = Task(
        title=clean_title,
        description=description.strip() or None,
        priority=task_priority,
        deadline=deadline,
        user_id=user.id,
    )
    session.add(task)
    await session.flush()
    add_task_history(session, user.id, "create", task.title, task.id)
    await session.commit()
    await invalidate_task_stats(user.id)
    await task_connection_manager.broadcast_task_change(user.id, "create", task.id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/edit", response_class=HTMLResponse)
async def update_task(
    task_id: int,
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    deadline: Optional[date] = Form(None),
    is_done: bool = Form(False),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")
    
    task = await get_owned_task(task_id, user, session)
    task.title = clean_title
    task.description = description.strip() or None
    task.priority = priority if priority in TASK_PRIORITIES else "medium"
    task.deadline = deadline
    task.is_done = is_done
    task.updated_at = datetime.utcnow()
    add_task_history(session, user.id, "update", task.title, task.id)

    await session.commit()
    await invalidate_task_stats(user.id)
    await task_connection_manager.broadcast_task_change(user.id, "update", task.id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/toggle", response_class=HTMLResponse)
async def toggle_task(
    task_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    task = await get_owned_task(task_id, user, session)
    task.is_done = not task.is_done
    task.updated_at = datetime.utcnow()
    add_task_history(session, user.id, "toggle", task.title, task.id)

    await session.commit()
    await invalidate_task_stats(user.id)
    await task_connection_manager.broadcast_task_change(user.id, "toggle", task.id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/delete", response_class=HTMLResponse)
async def delete_task(
    task_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    task = await get_owned_task(task_id, user, session)
    deleted_task_id = task.id
    deleted_task_title = task.title
    add_task_history(session, user.id, "delete", deleted_task_title)
    await session.delete(task)
    await session.commit()
    await invalidate_task_stats(user.id)
    await task_connection_manager.broadcast_task_change(user.id, "delete", deleted_task_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

