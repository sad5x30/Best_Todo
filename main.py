
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_users import FastAPIUsers

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_

from database import get_db
from models.tasks import Task
from models.users import User
from services.auth.auth_schemas import UserCreate, UserRead
from services.auth.fastapi_manager import auth_backend, get_user_manager
from services.tasks_cache import (
    get_cached_task_stats,
    set_cached_task_stats,
)
from services.auth.auth_routes import router as auth_router

from routes.tasks_route import router as tasks_router
from routes.tasks_ws import router as tasks_ws_router

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

TASK_PRIORITIES = {"low", "medium", "high"}
TASK_PRIORITY_LABELS = {
    "low": "Низкий",
    "medium": "Средний",
    "high": "Высокий",
}

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])
current_user = fastapi_users.current_user(optional=True)
current_active_user = fastapi_users.current_user()

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(tasks_ws_router)


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    priority: str = Query("all"),
    status_filter: str = Query("all", alias="status"),
    search_query: str = Query("", alias="search", max_length=120),
    page: int = Query(1, ge=1),
    user: Optional[User] = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    tasks = []
    all_tasks = []
    per_page = 5
    has_previous = False
    has_next = False
    total_tasks = 0
    total_pages = 1
    cached_stats = None

    active_priority = priority if priority in TASK_PRIORITIES else "all"
    active_status = status_filter if status_filter in {"done", "active"} else "all"
    active_search = search_query.strip()

    if user:
        all_result = await session.execute(
            select(Task).where(Task.user_id == user.id)
        )
        all_tasks = all_result.scalars().all()

        cached_stats = await get_cached_task_stats(user.id)

        if cached_stats is None:
            cached_stats = {
                "total": len(all_tasks),
                "done": sum(1 for task in all_tasks if task.is_done),
                "active": sum(1 for task in all_tasks if not task.is_done),
                "high": sum(1 for task in all_tasks if task.priority == "high"),
                "medium": sum(1 for task in all_tasks if task.priority == "medium"),
                "low": sum(1 for task in all_tasks if task.priority == "low"),
            }

            await set_cached_task_stats(user.id, cached_stats)

        query = select(Task).where(Task.user_id == user.id)

        if active_priority != "all":
            query = query.where(Task.priority == active_priority)

        if active_status == "done":
            query = query.where(Task.is_done.is_(True))
        elif active_status == "active":
            query = query.where(Task.is_done.is_(False))

        if active_search:
            search_pattern = f"%{active_search}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_tasks = await session.scalar(count_query)

        total_pages = (total_tasks + per_page -1) // per_page

        offset = (page - 1) * per_page

        result = await session.execute(
            query
            .order_by(Task.is_done.asc(), Task.updated_at.desc())
            .offset(offset)
            .limit(per_page)
        )

        tasks = result.scalars().all()

        has_previous = page > 1
        has_next = page < total_pages

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "tasks": tasks,
            "all_tasks": all_tasks,
            "active_priority": active_priority,
            "active_status": active_status,
            "active_search": active_search,
            "priority_labels": TASK_PRIORITY_LABELS,
            "page": page,
            "has_previous": has_previous,
            "has_next": has_next,
            "total_pages": total_pages,
            "total_tasks": total_tasks,
            "tasks_cache": cached_stats,
        },
    )
