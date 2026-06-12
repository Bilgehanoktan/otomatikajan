import pytest
from fastapi.testclient import TestClient
from apps.bilgeapi.main import app
from apps.bilgeapi.config import settings

def test_health_version_aligns_with_settings(monkeypatch):
    # Override settings.BILGEAPI_VERSION to verify dynamic resolution
    monkeypatch.setattr(settings, "BILGEAPI_VERSION", "1.2.0")
    
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.2.0"
    assert data["service"] == "bilgeapi"
    assert "status" in data

def test_ops_health_version_aligns_with_settings(monkeypatch):
    from apps.bilgeapi.auth import require_permission
    
    monkeypatch.setattr(settings, "BILGEAPI_VERSION", "1.2.0")
    
    # Override authentication dependencies for testing /v1/ops/health
    app.dependency_overrides[require_permission("bilgeapi.admin")] = lambda: {"user_id": "admin-test"}
    
    try:
        client = TestClient(app)
        response = client.get("/v1/ops/health")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.2.0"
        assert data["service"] == "bilgeapi"
    finally:
        app.dependency_overrides.clear()
