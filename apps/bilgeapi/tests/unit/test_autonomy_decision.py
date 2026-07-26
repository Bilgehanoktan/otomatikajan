import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from bilgeapi.main import app
from bilgeapi.config import settings, AutonomyMode
from bilgeapi.auth import get_current_identity
from bilgeapi.schemas.incident import IncidentCreate, Severity
from bilgeapi.services.autonomy_decision import IncidentClassifier, AutonomyDecisionEngine

class MockIncident:
    def __init__(self, severity="LOW", environment="development", kind="generic", error_message="something", tags=None, correlation_id="req_123"):
        self.severity = severity
        self.environment = environment
        self.kind = kind
        self.error_message = error_message
        self.stack_trace = None
        self.tags = tags or []
        self.correlation_id = correlation_id

def test_incident_classifier():
    classifier = IncidentClassifier()

    # 1. Security Breach classification
    inc_sec = MockIncident(error_message="unauthorized access to admin credentials")
    assert classifier.classify(inc_sec) == "SECURITY_BREACH"

    # 2. Database Failure classification
    inc_db = MockIncident(error_message="failed connection pool: sqlite database deadlock")
    assert classifier.classify(inc_db) == "DATABASE_FAILURE"

    # 3. API Gateway Timeout classification
    inc_time = MockIncident(error_message="gateway bad gateway 502 connection timed out")
    assert classifier.classify(inc_time) == "API_GATEWAY_TIMEOUT"

    # 4. Liveness Probe Fail classification
    inc_live = MockIncident(error_message="liveness unhealthy probe check failed")
    assert classifier.classify(inc_live) == "LIVENESS_PROBE_FAIL"

    # 5. Resource Exhaustion classification
    inc_res = MockIncident(error_message="disk memory OOM cpu exhausted")
    assert classifier.classify(inc_res) == "RESOURCE_EXHAUSTION"

    # 6. Unknown fallback classification
    inc_unk = MockIncident(error_message="generic weird error occurred")
    assert classifier.classify(inc_unk) == "UNKNOWN_ANOMALY"

def test_risk_calculation():
    engine = AutonomyDecisionEngine(None, None)

    # Low severity, dev env, safe action -> 10 + 0 + 0 = 10 (LOW)
    inc1 = MockIncident(severity="LOW", environment="development")
    score, level = engine.calculate_risk(inc1, "clear_local_cache")
    assert score == 10.0
    assert level == "LOW"

    # Critical severity, prod env, container restart -> 75 + 15 + 30 = 120 (Capped at 100, CRITICAL)
    inc2 = MockIncident(severity="CRITICAL", environment="production")
    score, level = engine.calculate_risk(inc2, "container_restart")
    assert score == 100.0
    assert level == "CRITICAL"

    # Medium severity, staging env, stuck job cancel -> 25 + 5 + 10 = 40 (MEDIUM)
    inc3 = MockIncident(severity="MEDIUM", environment="staging")
    score, level = engine.calculate_risk(inc3, "stuck_job_cancel")
    assert score == 40.0
    assert level == "MEDIUM"

def test_autonomy_decision_endpoint_requires_admin_auth(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    client = TestClient(app)
    response = client.post("/v1/system/autonomy/decide", json={"incident_id": "inc_123"})
    assert response.status_code == 401

def test_autonomy_decision_flow(monkeypatch, test_client):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    app.dependency_overrides[get_current_identity] = lambda: {"id": "admin-test", "role": "ADMIN", "type": "system"}

    # Register an incident to test against
    from bilgeapi.routers.deps import get_incident_repository
    incident_repo = app.dependency_overrides[get_incident_repository]()
    
    incident = IncidentCreate(
        project_key="test-app",
        source_system="gateway",
        environment="development",
        kind="database",
        severity=Severity.LOW,
        error_message="db connection lost",
        occurred_at=datetime.now(timezone.utc),
        correlation_id="corr-123"
    )
    created_incident = test_client.post(
        "/v1/incidents",
        json=incident.model_dump(mode="json"),
        headers={"X-API-Key": "any_key_since_auth_overridden"}
    ).json()
    incident_id = created_incident["id"]

    try:
        # Case 1: Autonomy OFF
        monkeypatch.setattr(settings, "BILGEAPI_AUTONOMY_MODE", "OFF")
        resp = test_client.post(
            "/v1/system/autonomy/decide",
            json={"incident_id": incident_id, "action_type": "clear_local_cache"},
            headers={"X-API-Key": "any_key"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligibility"] == "BLOCKED"
        assert "disabled" in data["decision_reason"].lower() or "off" in data["decision_reason"].lower()

        # Case 2: Autonomy OBSERVE_ONLY
        monkeypatch.setattr(settings, "BILGEAPI_AUTONOMY_MODE", "OBSERVE_ONLY")
        resp = test_client.post(
            "/v1/system/autonomy/decide",
            json={"incident_id": incident_id, "action_type": "clear_local_cache"},
            headers={"X-API-Key": "any_key"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligibility"] == "BLOCKED"
        assert "observe" in data["decision_reason"].lower()

        # Case 3: Autonomy SAFE_AUTONOMY (LOW risk action -> AUTO_RUN)
        monkeypatch.setattr(settings, "BILGEAPI_AUTONOMY_MODE", "SAFE_AUTONOMY")
        resp = test_client.post(
            "/v1/system/autonomy/decide",
            json={"incident_id": incident_id, "action_type": "clear_local_cache"},
            headers={"X-API-Key": "any_key"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligibility"] == "AUTO_RUN"
        assert data["requires_human_gate"] is False
        assert data["risk_level"] == "LOW"

        # Case 4: Autonomy SAFE_AUTONOMY (HIGH risk proposed action -> HUMAN_GATE_REQUIRED)
        resp = test_client.post(
            "/v1/system/autonomy/decide",
            json={"incident_id": incident_id, "action_type": "production_config_change"},
            headers={"X-API-Key": "any_key"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligibility"] == "HUMAN_GATE_REQUIRED"
        assert data["requires_human_gate"] is True
        assert data["human_gate_type"] == "remediation_approval"

    finally:
        app.dependency_overrides.clear()
