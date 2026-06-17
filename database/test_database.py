from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from alembic.config import Config
import dotenv
import os

dotenv.load_dotenv()
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or Config(
    "test_alembic.ini"
).get_main_option("sqlalchemy.url")

tests_engine = create_async_engine(TEST_DATABASE_URL, echo=True, poolclass=NullPool)
Base = declarative_base()

async_session = sessionmaker(
    tests_engine, expire_on_commit=False, class_=AsyncSession
)


async def override_get_db():
    async with async_session() as session:
        yield session
