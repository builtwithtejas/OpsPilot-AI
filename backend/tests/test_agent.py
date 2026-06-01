import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
API_KEY = "your-test-key"
HEADERS = {"X-API-Key": API_KEY}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_incidents_empty():
    r = client.get("/incidents/", headers=HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_projects_empty():
    r = client.get("/projects/", headers=HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_forecast_empty():
    r = client.get("/forecast/", headers=HEADERS)
    assert r.status_code == 200
    assert "forecasts" in r.json()


def test_webhook_gitlab_non_pipeline():
    r = client.post(
        "/webhooks/gitlab",
        json={"object_kind": "push"},
        headers={"X-Gitlab-Token": ""},
    )
    assert r.status_code == 200
    assert "not processed" in r.json()["message"]