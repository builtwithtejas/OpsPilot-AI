# backend/tests/conftest.py
# FIX: Fully async conftest — uses AsyncSession to match the app's get_db dependency.
# pytest-asyncio handles the event loop automatically with asyncio_mode = auto.

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database.database import Base
from app.database.dependencies import get_db
from app.main import app

# Isolated async SQLite for every test session
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_opspilot.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once for the test session, drop them on teardown."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def override_db():
    """Override get_db with the test async session for every test."""
    async def _override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    """Async HTTP client that talks directly to the FastAPI app in-process."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac