# backend/tests/test_incidents.py
# FIX: All tests converted to async def using the async client fixture.
# Run with:  API_KEY=test-key pytest tests/ -v

import pytest
from app.core.config import settings

API_KEY = settings.API_KEY
HEADERS = {"X-API-Key": API_KEY}


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

async def test_incidents_requires_auth(client):
    r = await client.get("/incidents/")
    assert r.status_code == 401

async def test_incidents_wrong_key(client):
    r = await client.get("/incidents/", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401

async def test_projects_requires_auth(client):
    r = await client.get("/projects/")
    assert r.status_code == 401

async def test_forecast_requires_auth(client):
    r = await client.get("/forecast/")
    assert r.status_code == 401


# ── Health (public) ───────────────────────────────────────────────

async def test_health_public(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

async def test_root_public(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "running"


# ── Incident CRUD ─────────────────────────────────────────────────

async def test_list_incidents_empty(client):
    r = await client.get("/incidents/", headers=HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

async def test_create_incident(client):
    r = await client.post("/incidents/", json=incident_payload(), headers=HEADERS)
    assert r.status_code == 201
    data = r.json()
    assert data["severity"] == "High"
    assert data["confidence"] == 85
    assert data["status"] == "Open"
    assert "id" in data
    assert "created_at" in data

async def test_get_incident_by_id(client):
    created = (await client.post("/incidents/", json=incident_payload(), headers=HEADERS)).json()
    r = await client.get(f"/incidents/{created['id']}", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]

async def test_get_incident_not_found(client):
    r = await client.get("/incidents/999999", headers=HEADERS)
    assert r.status_code == 404

async def test_patch_incident_status(client):
    created = (await client.post("/incidents/", json=incident_payload(), headers=HEADERS)).json()
    r = await client.patch(f"/incidents/{created['id']}", json={"status": "Resolved"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "Resolved"

async def test_patch_incident_not_found(client):
    r = await client.patch("/incidents/999999", json={"status": "Resolved"}, headers=HEADERS)
    assert r.status_code == 404

async def test_delete_incident(client):
    created = (await client.post("/incidents/", json=incident_payload(), headers=HEADERS)).json()
    del_r = await client.delete(f"/incidents/{created['id']}", headers=HEADERS)
    assert del_r.status_code == 204
    get_r = await client.get(f"/incidents/{created['id']}", headers=HEADERS)
    assert get_r.status_code == 404

async def test_delete_incident_not_found(client):
    r = await client.delete("/incidents/999999", headers=HEADERS)
    assert r.status_code == 404


# ── Search ────────────────────────────────────────────────────────

async def test_search_incidents(client):
    title = "UniqueSearchKeyword123"
    await client.post("/incidents/", json=incident_payload(title=title + " incident"), headers=HEADERS)
    r = await client.get(f"/incidents/?search={title}", headers=HEADERS)
    assert r.status_code == 200
    results = r.json()
    assert any(title in inc["title"] for inc in results)


# ── Validation ────────────────────────────────────────────────────

async def test_create_incident_invalid_severity(client):
    r = await client.post("/incidents/", json=incident_payload(severity="UNKNOWN"), headers=HEADERS)
    assert r.status_code == 422

async def test_create_incident_title_too_short(client):
    r = await client.post("/incidents/", json=incident_payload(title="ab"), headers=HEADERS)
    assert r.status_code == 422

async def test_create_incident_confidence_out_of_range(client):
    r = await client.post("/incidents/", json=incident_payload(confidence=150), headers=HEADERS)
    assert r.status_code == 422

async def test_create_incident_missing_required_fields(client):
    r = await client.post("/incidents/", json={"title": "Missing fields"}, headers=HEADERS)
    assert r.status_code == 422


# ── Pagination ────────────────────────────────────────────────────

async def test_pagination_skip_limit(client):
    for i in range(3):
        await client.post("/incidents/", json=incident_payload(title=f"Pagination test {i} incident"), headers=HEADERS)
    r = await client.get("/incidents/?skip=0&limit=2", headers=HEADERS)
    assert r.status_code == 200
    assert len(r.json()) <= 2

async def test_pagination_invalid_limit(client):
    r = await client.get("/incidents/?limit=9999", headers=HEADERS)
    assert r.status_code == 422


# ── Audit log ─────────────────────────────────────────────────────

async def test_audit_log_on_create(client):
    created = (await client.post("/incidents/", json=incident_payload(), headers=HEADERS)).json()
    r = await client.get(f"/incidents/{created['id']}/audit", headers=HEADERS)
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) >= 1
    assert any(l["action"] == "created" for l in logs)

async def test_audit_log_on_status_change(client):
    created = (await client.post("/incidents/", json=incident_payload(), headers=HEADERS)).json()
    await client.patch(f"/incidents/{created['id']}", json={"status": "In Progress"}, headers=HEADERS)
    r = await client.get(f"/incidents/{created['id']}/audit", headers=HEADERS)
    logs = r.json()
    assert any(l["action"] == "status_changed" for l in logs)


# ── Projects ─────────────────────────────────────────────────────

async def test_list_projects_empty(client):
    r = await client.get("/projects/", headers=HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

async def test_create_project(client):
    r = await client.post("/projects/", json={
        "gitlab_project_id": "test-project-999",
        "name": "Test Project",
        "description": "A test project",
    }, headers=HEADERS)
    assert r.status_code in (200, 201, 409)


# ── Forecast ─────────────────────────────────────────────────────

async def test_forecast_endpoint(client):
    r = await client.get("/forecast/", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "forecasts" in data
    assert isinstance(data["forecasts"], list)