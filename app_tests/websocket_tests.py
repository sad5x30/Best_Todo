from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from database.test_database import async_session
from main import app
from models.users import User
from services.auth.fastapi_manager import password_helper
from routes import tasks_ws


async def create_test_user() -> User:
    async with async_session() as session:
        unique_id = uuid4().hex
        user = User(
            email=f"ws-{unique_id}@gmail.com",
            username=f"ws-{unique_id}",
            hashed_password=password_helper.hash("testpassword"),
            is_active=True,
        )
        session.add(user)
        await session.commit()
        return user


def test_tasks_websocket_rejects_anonymous_client():
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/tasks"):
                pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


@pytest.mark.asyncio
async def test_tasks_websocket_receives_task_change_for_logged_in_user(monkeypatch):
    monkeypatch.setattr(tasks_ws, "async_session", async_session)
    user = await create_test_user()

    with TestClient(app) as client:
        login_response = client.post(
            "/auth/login",
            data={
                "username": user.email,
                "password": "testpassword",
            },
        )
        assert login_response.status_code in [200, 204]

        with client.websocket_connect("/ws/tasks") as websocket:
            create_response = client.post(
                "/tasks",
                data={
                    "title": f"Realtime Task {uuid4().hex}",
                    "description": "Should broadcast",
                    "priority": "medium",
                },
                follow_redirects=False,
            )

            assert create_response.status_code == 303
            message = websocket.receive_json()

    assert message["type"] == "task_changed"
    assert message["action"] == "create"
    assert isinstance(message["task_id"], int)
