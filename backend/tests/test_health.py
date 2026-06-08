"""Basic smoke tests for OpsPilot AI.

H-1 FIX: The app uses an async lifespan and async DB dependencies.
Using the sync TestClient with an async app causes hangs/errors.
Replaced with pytest-anyio + httpx.AsyncClient (ASGI transport).

Requirements (add to requirements.txt / dev dependencies):
  anyio[trio]>=3.7
  httpx>=0.27
  pytest-anyio>=0.0.0   # or anyio's pytest plugin via: pip install anyio[pytest]
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings

# H-1 FIX: Override the default async DB dependency so tests use a fresh
# SQLite in-memory database instead of the production Neon Postgres URL.
from app.database.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.database.database import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
_TestSession = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with _TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables():
    """Create all tables in the in-memory SQLite DB once per test session."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await _test_engine.dispose()


API_KEY = settings.API_KEY
HEADERS = {"X-API-Key": API_KEY}


@pytest.mark.anyio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_incidents_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/incidents/")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_and_get_incident():
    payload = {
        "title": "Test deployment failure",
        "severity": "High",
        "status": "Open",
        "description": "Deployment pipeline failed on main branch during build step.",
        "remediation": "1. Check build logs. 2. Fix dependency. 3. Redeploy.",
        "confidence": 85,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post("/incidents/", json=payload, headers=HEADERS)
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["severity"] == "High"
        assert created["confidence"] == 85

        get_resp = await client.get(f"/incidents/{created['id']}", headers=HEADERS)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == created["id"]


@pytest.mark.anyio
async def test_patch_incident():
    payload = {
        "title": "Patch test incident",
        "severity": "Low",
        "status": "Open",
        "description": "Minor issue detected in staging environment.",
        "remediation": "Restart the service.",
        "confidence": 60,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = (await client.post("/incidents/", json=payload, headers=HEADERS)).json()
        patched = await client.patch(
            f"/incidents/{created['id']}",
            json={"status": "Resolved"},
            headers=HEADERS,
        )
    assert patched.status_code == 200
    assert patched.json()["status"] == "Resolved"


@pytest.mark.anyio
async def test_delete_incident():
    payload = {
        "title": "Delete test incident",
        "severity": "Medium",
        "status": "Open",
        "description": "Temporary incident for delete test.",
        "remediation": "No action needed.",
        "confidence": 50,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = (await client.post("/incidents/", json=payload, headers=HEADERS)).json()
        del_resp = await client.delete(f"/incidents/{created['id']}", headers=HEADERS)
        assert del_resp.status_code == 204

        get_resp = await client.get(f"/incidents/{created['id']}", headers=HEADERS)
        assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_incident_validation():
    bad_payload = {"title": "x", "severity": "UNKNOWN", "confidence": 999}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/incidents/", json=bad_payload, headers=HEADERS)
    assert response.status_code == 422
