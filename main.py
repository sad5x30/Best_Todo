from datetime import date, datetime
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_users import FastAPIUsers
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.tasks import Task
from models.users import User
from services.auth.auth_schemas import UserCreate, UserRead
from services.auth.fastapi_manager import auth_backend, get_user_manager


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])
current_user = fastapi_users.current_user(optional=True)
current_active_user = fastapi_users.current_user()

TASK_PRIORITIES = {"low", "medium", "high"}
TASK_PRIORITY_LABELS = {
    "low": "Низкий",
    "medium": "Средний",
    "high": "Высокий",
}

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


@app.post("/logout", response_class=HTMLResponse)
async def logout():
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("boba")
    return response


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    priority: str = Query("all"),
    status_filter: str = Query("all", alias="status"),
    user: Optional[User] = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    tasks = []
    all_tasks = []
    active_priority = priority if priority in TASK_PRIORITIES else "all"
    active_status = status_filter if status_filter in {"done", "active"} else "all"

    if user:
        all_result = await session.execute(
            select(Task).where(Task.user_id == user.id)
        )
        all_tasks = all_result.scalars().all()

        query = select(Task).where(Task.user_id == user.id)

        if active_priority != "all":
            query = query.where(Task.priority == active_priority)

        if active_status == "done":
            query = query.where(Task.is_done.is_(True))
        elif active_status == "active":
            query = query.where(Task.is_done.is_(False))

        result = await session.execute(
            query.order_by(Task.is_done.asc(), Task.updated_at.desc())
        )
        tasks = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "tasks": tasks,
            "all_tasks": all_tasks,
            "active_priority": active_priority,
            "active_status": active_status,
            "priority_labels": TASK_PRIORITY_LABELS,
        },
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


@app.post("/tasks", response_class=HTMLResponse)
async def create_task(
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    deadline: Optional[date] = Form(None),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    task_priority = priority if priority in TASK_PRIORITIES else "medium"

    session.add(
        Task(
            title=title.strip(),
            description=description.strip() or None,
            priority=task_priority,
            deadline=deadline,
            user_id=user.id,
        )
    )
    await session.commit()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/tasks/{task_id}/edit", response_class=HTMLResponse)
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
    task = await get_owned_task(task_id, user, session)
    task.title = title.strip()
    task.description = description.strip() or None
    task.priority = priority if priority in TASK_PRIORITIES else "medium"
    task.deadline = deadline
    task.is_done = is_done
    task.updated_at = datetime.utcnow()

    await session.commit()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/tasks/{task_id}/toggle", response_class=HTMLResponse)
async def toggle_task(
    task_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    task = await get_owned_task(task_id, user, session)
    task.is_done = not task.is_done
    task.updated_at = datetime.utcnow()

    await session.commit()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/tasks/{task_id}/delete", response_class=HTMLResponse)
async def delete_task(
    task_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    task = await get_owned_task(task_id, user, session)
    await session.delete(task)
    await session.commit()

    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/registration.html")


@app.get("/auth/login", response_class=HTMLResponse, include_in_schema=False)
async def auth_login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@app.get("/auth/register", response_class=HTMLResponse, include_in_schema=False)
async def auth_register_page(request: Request):
    return templates.TemplateResponse(request, "auth/registration.html")
