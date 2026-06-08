# backend/tests/test_incidents.py
# Complete test suite covering auth, CRUD, validation, and edge cases.
# Replaces the old test_agent.py which had a hardcoded wrong API key.
#
# Run with:
#   DATABASE_URL=sqlite:///./test.db API_KEY=test-key pytest tests/ -v

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)

# FIX: Read API key from settings — no more hardcoded "your-test-key"
API_KEY = settings.API_KEY
HEADERS = {"X-API-Key": API_KEY}

# Reusable valid incident payload
def incident_payload(**overrides):
    base = {
        "title": "Test deployment failure on main branch",
        "severity": "High",
        "status": "Open",
        "description": "Deployment pipeline failed on main branch during build step.",
        "remediation": "1. Check build logs. 2. Fix dependency. 3. Redeploy.",
        "confidence": 85,
    }
    base.update(overrides)
    return base


# ── Auth tests ────────────────────────────────────────────────────

def test_incidents_requires_auth():
    r = client.get("/incidents/")
    assert r.status_code == 401

def test_incidents_wrong_key():
    r = client.get("/incidents/", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401

def test_projects_requires_auth():
    r = client.get("/projects/")
    assert r.status_code == 401

def test_forecast_requires_auth():
    r = client.get("/forecast/")
    assert r.status_code == 401


# ── Health (public) ───────────────────────────────────────────────

def test_health_public():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_root_public():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "running"


# ── Incident CRUD ─────────────────────────────────────────────────

def test_list_incidents_empty():
    r = client.get("/incidents/", headers=HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_create_incident():
    r = client.post("/incidents/", json=incident_payload(), headers=HEADERS)
    assert r.status_code == 201
    data = r.json()
    assert data["severity"] == "High"
    assert data["confidence"] == 85
    assert data["status"] == "Open"
    assert "id" in data
    assert "created_at" in data

def test_get_incident_by_id():
    created = client.post("/incidents/", json=incident_payload(), headers=HEADERS).json()
    r = client.get(f"/incidents/{created['id']}", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]

def test_get_incident_not_found():
    r = client.get("/incidents/999999", headers=HEADERS)
    assert r.status_code == 404

def test_patch_incident_status():
    created = client.post("/incidents/", json=incident_payload(), headers=HEADERS).json()
    r = client.patch(f"/incidents/{created['id']}", json={"status": "Resolved"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "Resolved"

def test_patch_incident_not_found():
    r = client.patch("/incidents/999999", json={"status": "Resolved"}, headers=HEADERS)
    assert r.status_code == 404

def test_delete_incident():
    created = client.post("/incidents/", json=incident_payload(), headers=HEADERS).json()
    del_r = client.delete(f"/incidents/{created['id']}", headers=HEADERS)
    assert del_r.status_code == 204
    get_r = client.get(f"/incidents/{created['id']}", headers=HEADERS)
    assert get_r.status_code == 404

def test_delete_incident_not_found():
    r = client.delete("/incidents/999999", headers=HEADERS)
    assert r.status_code == 404


# ── Search ────────────────────────────────────────────────────────

def test_search_incidents():
    title = "UniqueSearchKeyword123"
    client.post("/incidents/", json=incident_payload(title=title + " incident"), headers=HEADERS)
    r = client.get(f"/incidents/?search={title}", headers=HEADERS)
    assert r.status_code == 200
    results = r.json()
    assert any(title in inc["title"] for inc in results)


# ── Validation ────────────────────────────────────────────────────

def test_create_incident_invalid_severity():
    r = client.post("/incidents/", json=incident_payload(severity="UNKNOWN"), headers=HEADERS)
    assert r.status_code == 422

def test_create_incident_title_too_short():
    r = client.post("/incidents/", json=incident_payload(title="ab"), headers=HEADERS)
    assert r.status_code == 422

def test_create_incident_confidence_out_of_range():
    r = client.post("/incidents/", json=incident_payload(confidence=150), headers=HEADERS)
    assert r.status_code == 422

def test_create_incident_missing_required_fields():
    r = client.post("/incidents/", json={"title": "Missing fields"}, headers=HEADERS)
    assert r.status_code == 422


# ── Pagination ────────────────────────────────────────────────────

def test_pagination_skip_limit():
    # Create 3 incidents
    for i in range(3):
        client.post("/incidents/", json=incident_payload(title=f"Pagination test {i} incident"), headers=HEADERS)
    r = client.get("/incidents/?skip=0&limit=2", headers=HEADERS)
    assert r.status_code == 200
    assert len(r.json()) <= 2

def test_pagination_invalid_limit():
    r = client.get("/incidents/?limit=9999", headers=HEADERS)
    assert r.status_code == 422     # limit is capped at 200 by Query(le=200)


# ── Audit log ─────────────────────────────────────────────────────

def test_audit_log_on_create():
    created = client.post("/incidents/", json=incident_payload(), headers=HEADERS).json()
    r = client.get(f"/incidents/{created['id']}/audit", headers=HEADERS)
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) >= 1
    assert any(l["action"] == "created" for l in logs)

def test_audit_log_on_status_change():
    created = client.post("/incidents/", json=incident_payload(), headers=HEADERS).json()
    client.patch(f"/incidents/{created['id']}", json={"status": "In Progress"}, headers=HEADERS)
    r = client.get(f"/incidents/{created['id']}/audit", headers=HEADERS)
    logs = r.json()
    assert any(l["action"] == "status_changed" for l in logs)


# ── Projects ─────────────────────────────────────────────────────

def test_list_projects_empty():
    r = client.get("/projects/", headers=HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_create_project():
    r = client.post("/projects/", json={
        "gitlab_project_id": "test-project-999",
        "name": "Test Project",
        "description": "A test project",
    }, headers=HEADERS)
    # 201 created or 409 if already exists from a previous run
    assert r.status_code in (200, 201, 409)


# ── Forecast ─────────────────────────────────────────────────────

def test_forecast_endpoint():
    r = client.get("/forecast/", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "forecasts" in data
    assert isinstance(data["forecasts"], list)
