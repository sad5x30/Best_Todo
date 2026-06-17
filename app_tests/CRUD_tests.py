import sys
from uuid import uuid4
from pathlib import Path

from httpx import AsyncClient, ASGITransport
import pytest
import pytest_asyncio
from sqlalchemy import select

from alembic.config import Config
from alembic import command

sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app
from database.test_database import override_get_db, async_session
from database.database import get_db

from models.users import User
from models.tasks import Task, TaskHistory

from services.auth.fastapi_manager import password_helper
transport = ASGITransport(app=app)

@pytest_asyncio.fixture(scope="session", autouse=True)
def apply_migrations():

    alembic_cfg = Config("test_alembic.ini")

    command.upgrade(
        alembic_cfg,
        "head",
    )

    yield

@pytest.fixture(autouse=True)
def override_db():

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_user():
    async with async_session() as session:
        unique_id = uuid4().hex
        
        user = User(
            email=f"test-{unique_id}@gmail.com",
            username=f"test-{unique_id}",
            hashed_password=password_helper.hash("testpassword"),
            is_active=True,
        )

        session.add(user)

        await session.commit()

        return user

@pytest_asyncio.fixture
async def auth_client(test_user):

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:

        response = await client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword"
            }
        )

        assert response.status_code in [200, 204]

        yield client    


async def get_user_task(user_id: int, title: str) -> Task | None:
    async with async_session() as session:
        result = await session.execute(
            select(Task).where(Task.user_id == user_id, Task.title == title)
        )
        return result.scalar_one_or_none()


async def get_task(task_id: int) -> Task | None:
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()


async def get_task_history(user_id: int, method: str, task_title: str) -> TaskHistory | None:
    async with async_session() as session:
        result = await session.execute(
            select(TaskHistory).where(
                TaskHistory.user_id == user_id,
                TaskHistory.method == method,
                TaskHistory.task_title == task_title,
            )
        )
        return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_create_task(auth_client, test_user):

    response = await auth_client.post(
        "/tasks",
        data={
            "title": "Test Task",
            "description": "Test",
            "priority": "high",
            "deadline": "2026-06-30",
        }
    )

    assert response.status_code == 303


    task = await get_user_task(test_user.id, "Test Task")

    assert task is not None
    assert task.description == "Test"
    assert task.priority == "high"
    assert task.deadline.isoformat() == "2026-06-30"
    assert task.is_done is False

    history = await get_task_history(test_user.id, "create", "Test Task")
    assert history is not None
    assert history.task_id == task.id


@pytest.mark.asyncio
async def test_create_task_requires_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False,
    ) as client:
        response = await client.post(
            "/tasks",
            data={
                "title": "Anonymous Task",
                "description": "Should not be created",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_task_normalizes_form_values(auth_client, test_user):
    unique_title = f"Normalized Task {uuid4().hex}"

    response = await auth_client.post(
        "/tasks",
        data={
            "title": f"  {unique_title}  ",
            "description": "   ",
            "priority": "urgent",
        },
    )

    assert response.status_code == 303

    task = await get_user_task(test_user.id, unique_title)
    assert task is not None
    assert task.description is None
    assert task.priority == "medium"


@pytest.mark.asyncio
async def test_update_task(auth_client, test_user):
    create_response = await auth_client.post(
        "/tasks",
        data={
            "title": "Task to Update",
            "description": "Before update",
            "priority": "low",
        },
    )
    assert create_response.status_code == 303

    task = await get_user_task(test_user.id, "Task to Update")
    assert task is not None

    update_response = await auth_client.post(
        f"/tasks/{task.id}/edit",
        data={
            "title": "Updated Task",
            "description": "After update",
            "priority": "high",
            "deadline": "2026-07-01",
            "is_done": "true",
        },
    )

    assert update_response.status_code == 303

    updated_task = await get_task(task.id)
    assert updated_task is not None
    assert updated_task.title == "Updated Task"
    assert updated_task.description == "After update"
    assert updated_task.priority == "high"
    assert updated_task.deadline.isoformat() == "2026-07-01"
    assert updated_task.is_done is True

    history = await get_task_history(test_user.id, "update", "Updated Task")
    assert history is not None
    assert history.task_id == task.id


@pytest.mark.asyncio
async def test_user_cannot_update_another_users_task(auth_client):
    async with async_session() as session:
        unique_id = uuid4().hex
        other_user = User(
            email=f"other-{unique_id}@gmail.com",
            username=f"other-{unique_id}",
            hashed_password=password_helper.hash("testpassword"),
            is_active=True,
        )
        session.add(other_user)
        await session.flush()

        other_task = Task(
            title=f"Other Task {unique_id}",
            description="Private",
            priority="low",
            user_id=other_user.id,
        )
        session.add(other_task)
        await session.commit()
        task_id = other_task.id

    response = await auth_client.post(
        f"/tasks/{task_id}/edit",
        data={
            "title": "Stolen Task",
            "description": "Changed",
            "priority": "high",
        },
    )

    assert response.status_code == 404

    task = await get_task(task_id)
    assert task is not None
    assert task.title != "Stolen Task"
    assert task.priority == "low"


@pytest.mark.asyncio
async def test_toggle_task(auth_client, test_user):
    create_response = await auth_client.post(
        "/tasks",
        data={
            "title": "Task to Toggle",
            "description": "Test",
            "priority": "medium",
        },
    )
    assert create_response.status_code == 303

    task = await get_user_task(test_user.id, "Task to Toggle")
    assert task is not None
    assert task.is_done is False

    toggle_response = await auth_client.post(f"/tasks/{task.id}/toggle")

    assert toggle_response.status_code == 303

    toggled_task = await get_task(task.id)
    assert toggled_task is not None
    assert toggled_task.is_done is True

    history = await get_task_history(test_user.id, "toggle", "Task to Toggle")
    assert history is not None
    assert history.task_id == task.id


@pytest.mark.asyncio
async def test_home_filters_tasks_for_authenticated_user(auth_client, test_user):
    unique_id = uuid4().hex
    matching_title = f"Matching Task {unique_id}"
    hidden_title = f"Hidden Task {unique_id}"

    async with async_session() as session:
        session.add_all(
            [
                Task(
                    title=matching_title,
                    description="find-me",
                    priority="high",
                    is_done=False,
                    user_id=test_user.id,
                ),
                Task(
                    title=hidden_title,
                    description="different",
                    priority="low",
                    is_done=True,
                    user_id=test_user.id,
                ),
            ]
        )
        await session.commit()

    response = await auth_client.get(
        "/",
        params={
            "priority": "high",
            "status": "active",
            "search": "find-me",
        },
    )

    assert response.status_code == 200
    assert matching_title in response.text
    assert hidden_title not in response.text


@pytest.mark.asyncio
async def test_deleting_task(auth_client, test_user):
    create_response = await auth_client.post(
        "/tasks",
        data = {
            "title": "Task to Delete",
            "description": "Test",
            "priority": "medium",
        }
    )

    assert create_response.status_code == 303

    task = await get_user_task(test_user.id, "Task to Delete")
    assert task is not None

    delete_response = await auth_client.post(f"/tasks/{task.id}/delete")
    assert delete_response.status_code == 303

    deleted_task = await get_task(task.id)
    assert deleted_task is None

    history = await get_task_history(test_user.id, "delete", "Task to Delete")
    assert history is not None
    assert history.task_id is None
