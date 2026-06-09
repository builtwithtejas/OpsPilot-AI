"""
Health and smoke tests for OpsPilot AI.

FIX: Removed the module-level app.dependency_overrides[get_db] = override_get_db
assignment. That override was being cleared by conftest.py's session-scoped
setup_test_db after the first test ran, causing all subsequent tests in this file
to hit the production Neon DB.

The DB override is now set once in conftest.py at session scope and applies
to every test in the suite automatically.

FIX: Removed duplicate CRUD tests that already exist in test_incidents.py.
This file now covers only health/auth/smoke paths.
"""

import pytest
from app.core.config import settings

API_KEY = settings.API_KEY
HEADERS = {"X-API-Key": API_KEY}


async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "service" in data
    assert "version" in data


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    # FIX: health.py router returns service, version, timestamp — assert them
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


async def test_favicon(client):
    response = await client.get("/favicon.ico")
    assert response.status_code == 204


async def test_incidents_requires_auth(client):
    response = await client.get("/incidents/")
    assert response.status_code == 401


async def test_invalid_api_key_rejected(client):
    response = await client.get("/incidents/", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


async def test_create_incident(client):
    payload = {
        "title": "Health test deployment failure",
        "severity": "High",
        "status": "Open",
        "description": "Deployment pipeline failed on main branch during build step.",
        "remediation": "1. Check build logs. 2. Fix dependency. 3. Redeploy.",
        "confidence": 85,
    }
    response = await client.post("/incidents/", json=payload, headers=HEADERS)
    assert response.status_code == 201
    data = response.json()
    assert data["severity"] == "High"
    assert data["confidence"] == 85


async def test_incident_validation(client):
    bad_payload = {"title": "x", "severity": "UNKNOWN", "confidence": 999}
    response = await client.post("/incidents/", json=bad_payload, headers=HEADERS)
    assert response.status_code == 422