import pytest
import pytest_asyncio
from database import get_db
from main import app
from database.test_database import override_get_db
from alembic.config import Config
from alembic import command


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
