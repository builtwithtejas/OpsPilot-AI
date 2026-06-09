import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database.database import Base
from app.database.dependencies import get_db
from app.main import app

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


async def _override_get_db():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once for the test session, drop them on teardown."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # FIX: Set the override once at session scope so it persists for the whole
    # test run. Previously override_db was function-scoped and called
    # dependency_overrides.clear() after each test — this wiped the module-level
    # override set by test_health.py, causing subsequent tests in that file to
    # hit the production Neon DB instead of the SQLite test DB.
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    """Async HTTP client that talks directly to the FastAPI app in-process."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac