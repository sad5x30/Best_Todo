from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from database.test_database import async_session
from main import app
from models.users import User
from services.auth.fastapi_manager import password_helper

transport = ASGITransport(app=app)


@pytest_asyncio.fixture
async def user_db():
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


async def get_user_by_email(email: str) -> User | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_login(user_db):
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        
        response = await client.post(
            "/auth/login",
            data={
                "username": user_db.email,
                "password": "testpassword",
            }
        )
        assert response.status_code in [200, 204], response.text


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(user_db):
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:

        response = await client.post(
            "/auth/login",
            data={
                "username": user_db.email,
                "password": "wrong-password",
            }
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_register():
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        
        unique_id = uuid4().hex
        email = f"test-{unique_id}@gmail.com"
        username = f"test-{unique_id}"
        
        response = await client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "testpassword",
            }
        )

        assert response.status_code in [200, 201], response.text

        created_user = await get_user_by_email(email)
        assert created_user is not None
        assert created_user.username == username
        assert password_helper.verify_and_update("testpassword", created_user.hashed_password)[0]


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(user_db):
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:

        response = await client.post(
            "/auth/register",
            json={
                "email": user_db.email,
                "username": f"duplicate-{uuid4().hex}",
                "password": "testpassword",
            }
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_logout_redirects_and_clears_auth_cookie():
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=False,
    ) as client:

        response = await client.post("/logout")

        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert "boba=" in response.headers["set-cookie"]
        assert "Max-Age=0" in response.headers["set-cookie"]
