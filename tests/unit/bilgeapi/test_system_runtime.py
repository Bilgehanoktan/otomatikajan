import os
import pytest
from fastapi.testclient import TestClient

from apps.bilgeapi.main import app
from apps.bilgeapi.config import settings, AutonomyMode
from apps.bilgeapi.auth import require_permission

def test_system_release_requires_admin_auth(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    client = TestClient(app)
    # Without authentication dependency override, should return 401
    response = client.get("/v1/system/release")
    assert response.status_code == 401

def test_system_release_metadata_authenticated(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    from apps.bilgeapi.auth import get_current_identity
    app.dependency_overrides[get_current_identity] = lambda: {"id": "admin-test", "role": "ADMIN", "type": "system"}
    
    try:
        client = TestClient(app)
        response = client.get("/v1/system/release")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "bilgeapi"
        assert data["version"] == settings.BILGEAPI_VERSION
        assert data["environment"] == settings.APP_ENV
        assert "git_commit" in data
        assert "git_tag" in data
        assert "python_version" in data
        assert "dependencies" in data
        assert "fastapi" in data["dependencies"]
    finally:
        app.dependency_overrides.clear()

def test_system_autonomy_registry_authenticated(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    from apps.bilgeapi.auth import get_current_identity
    app.dependency_overrides[get_current_identity] = lambda: {"id": "admin-test", "role": "ADMIN", "type": "system"}
    monkeypatch.setattr(settings, "BILGEAPI_AUTONOMY_MODE", "SAFE_AUTONOMY")
    
    try:
        client = TestClient(app)
        response = client.get("/v1/system/autonomy")
        assert response.status_code == 200
        data = response.json()
        assert data["active_autonomy_mode"] == "SAFE_AUTONOMY"
        assert data["observe_only"] is False
        assert data["safe_actions_enabled"] is True
        assert len(data["allowed_safe_actions"]) > 0
        assert "clear_local_cache" in data["allowed_safe_actions"]
        assert "container_restart" in data["human_gate_required_actions"]
    finally:
        app.dependency_overrides.clear()

def test_system_autonomy_default_observe_only_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BILGEAPI_AUTONOMY_MODE", "")
    
    # Trigger dynamic resolution
    assert settings.BILGEAPI_AUTONOMY_MODE == "OBSERVE_ONLY"

def test_system_autonomy_default_safe_autonomy_in_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("BILGEAPI_AUTONOMY_MODE", "")
    
    assert settings.BILGEAPI_AUTONOMY_MODE == "SAFE_AUTONOMY"

def test_system_autonomy_invalid_value_fallback(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BILGEAPI_AUTONOMY_MODE", "INVALID_MODE_VALUE_XYZ")
    
    assert settings.BILGEAPI_AUTONOMY_MODE == "OBSERVE_ONLY"
