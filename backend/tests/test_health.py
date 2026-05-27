"""Basic smoke tests for OpsPilot AI."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)

API_KEY = settings.API_KEY
HEADERS = {"X-API-Key": API_KEY}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_incidents_requires_auth():
    response = client.get("/incidents/")
    assert response.status_code == 401


def test_create_and_get_incident():
    payload = {
        "title": "Test deployment failure",
        "severity": "High",
        "status": "Open",
        "description": "Deployment pipeline failed on main branch during build step.",
        "remediation": "1. Check build logs. 2. Fix dependency. 3. Redeploy.",
        "confidence": 85,
    }
    create_resp = client.post("/incidents/", json=payload, headers=HEADERS)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["severity"] == "High"
    assert created["confidence"] == 85

    get_resp = client.get(f"/incidents/{created['id']}", headers=HEADERS)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == created["id"]


def test_patch_incident():
    payload = {
        "title": "Patch test incident",
        "severity": "Low",
        "status": "Open",
        "description": "Minor issue detected in staging environment.",
        "remediation": "Restart the service.",
        "confidence": 60,
    }
    created = client.post("/incidents/", json=payload, headers=HEADERS).json()
    patched = client.patch(
        f"/incidents/{created['id']}",
        json={"status": "Resolved"},
        headers=HEADERS,
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "Resolved"


def test_delete_incident():
    payload = {
        "title": "Delete test incident",
        "severity": "Medium",
        "status": "Open",
        "description": "Temporary incident for delete test.",
        "remediation": "No action needed.",
        "confidence": 50,
    }
    created = client.post("/incidents/", json=payload, headers=HEADERS).json()
    del_resp = client.delete(f"/incidents/{created['id']}", headers=HEADERS)
    assert del_resp.status_code == 204

    get_resp = client.get(f"/incidents/{created['id']}", headers=HEADERS)
    assert get_resp.status_code == 404


def test_incident_validation():
    bad_payload = {"title": "x", "severity": "UNKNOWN", "confidence": 999}
    response = client.post("/incidents/", json=bad_payload, headers=HEADERS)
    assert response.status_code == 422
