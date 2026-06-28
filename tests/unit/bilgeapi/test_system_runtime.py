import os
import pytest
from fastapi.testclient import TestClient

from apps.bilgeapi.main import app
from apps.bilgeapi.config import settings, AutonomyMode
from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.services.self_healing import SelfHealingPolicy

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


def test_management_gate_default_locked_authenticated(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED", False)
    from apps.bilgeapi.auth import get_current_identity
    app.dependency_overrides[get_current_identity] = lambda: {"id": "admin-test", "role": "ADMIN", "type": "system"}

    try:
        client = TestClient(app)
        response = client.get("/v1/system/management-gate")
        assert response.status_code == 200
        data = response.json()
        assert data["unlocked"] is False
        assert data["status"] == "LOCKED"
        assert "auto_deploy" in data["forbidden_actions"]
    finally:
        app.dependency_overrides.clear()


def test_management_gate_admin_can_toggle(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED", False)
    from apps.bilgeapi.auth import get_current_identity
    app.dependency_overrides[get_current_identity] = lambda: {"id": "admin-test", "role": "ADMIN", "type": "system"}

    try:
        client = TestClient(app)
        response = client.post(
            "/v1/system/management-gate",
            json={"unlocked": True, "reason": "unit test unlock"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unlocked"] is True
        assert data["status"] == "UNLOCKED"
        assert data["reason"] == "unit test unlock"
        assert settings.BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED is True
    finally:
        app.dependency_overrides.clear()
        monkeypatch.setattr(settings, "BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED", False)


def test_self_healing_policy_blocks_when_management_gate_locked(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)
    monkeypatch.setattr(settings, "BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED", False)

    decision = SelfHealingPolicy().evaluate(
        {"severity": "LOW"},
        {
            "action_type": "restart_worker",
            "execution_mode": "AUTO_SAFE",
            "requires_human_gate": False,
        },
    )

    assert decision["allowed"] is False
    assert decision["requires_human_gate"] is True
    assert "Management actions are locked" in decision["reason"]


def test_self_healing_policy_allows_safe_action_when_management_gate_unlocked(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS", ["restart_worker"])
    monkeypatch.setattr(settings, "BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED", True)

    decision = SelfHealingPolicy().evaluate(
        {"severity": "LOW"},
        {
            "action_type": "restart_worker",
            "execution_mode": "AUTO_SAFE",
            "requires_human_gate": False,
        },
    )

    assert decision["allowed"] is True
    assert decision["requires_human_gate"] is False


def test_get_queue_status_unauthorized(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    client = TestClient(app)
    response = client.get("/v1/system/queue/status")
    assert response.status_code == 401


def test_get_queue_status_authorized(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    from apps.bilgeapi.auth import get_current_identity
    app.dependency_overrides[get_current_identity] = lambda: {"id": "admin-test", "role": "ADMIN", "type": "system"}

    try:
        client = TestClient(app)
        response = client.get("/v1/system/queue/status")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "status_counts" in data
        assert "active_leases" in data
        assert "orchestration_runs" in data
    finally:
        app.dependency_overrides.clear()


def test_seed_runbooks_endpoint(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    from apps.bilgeapi.auth import get_current_identity
    app.dependency_overrides[get_current_identity] = lambda: {"id": "admin-test", "role": "ADMIN", "type": "system"}

    try:
        client = TestClient(app)
        response = client.post("/v1/watchdog/runbooks/seed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Default runbooks seeded" in data["message"]
    finally:
        app.dependency_overrides.clear()

