import pytest
import jwt
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import status
from apps.bilgeapi.config import settings
from apps.bilgeapi.schemas.incident import IncidentResponse, Severity
from apps.bilgeapi.schemas.diagnostic import DiagnosticResult, DiagnosticStatus
from apps.bilgeapi.schemas.repair import ApprovalStatus, DispatchStatus
from apps.bilgeapi.services.risk import RiskScoringService

# Helpers to build mock models
def create_mock_incident(environment="development", severity="LOW", kind="backend"):
    return IncidentResponse(
        id="inc_123",
        project_key="test-project",
        source_system="app",
        environment=environment,
        kind=kind,
        severity=severity,
        error_message="Connection timeout database",
        occurred_at=datetime.now(timezone.utc),
        correlation_id="corr_123",
        tags=[],
        metadata={},
        created_at=datetime.now(timezone.utc)
    )

def create_mock_diagnostic(confidence=0.9, recommendations=None):
    if recommendations is None:
        recommendations = [{"description": "Increase connection pool size"}]
    return DiagnosticResult(
        diagnostic_id="diag_123",
        incident_id="inc_123",
        status=DiagnosticStatus.COMPLETED,
        summary="DB timeout detected",
        root_cause_hypothesis="exhaustion",
        confidence=confidence,
        risk_score=0.2,
        findings=[{"description": "Too many connections"}],
        recommendations=recommendations,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )

def test_risk_scoring_low_risk():
    service = RiskScoringService()
    incident = create_mock_incident(environment="development", severity="LOW", kind="backend")
    diagnostic = create_mock_diagnostic(confidence=1.0, recommendations=[{"description": "Check application traceback"}])
    score, reason = service.calculate_risk(incident, diagnostic)
    
    # Base Dev environment (+0.05), LOW severity (+0.10), kind backend (+0.05) -> 0.20
    assert score == 0.20
    assert "environment is development" in reason
    assert "severity is low" in reason

def test_risk_scoring_high_risk():
    service = RiskScoringService()
    # Production (+0.3), Critical severity (+0.4), Security kind (+0.2), uncertainty (+0.02)
    # Recommendation has delete keyword (+0.3)
    incident = create_mock_incident(environment="production", severity="CRITICAL", kind="security_vulnerability")
    diagnostic = create_mock_diagnostic(confidence=0.8, recommendations=[{"description": "Delete table schema_migration"}])
    score, reason = service.calculate_risk(incident, diagnostic)
    
    # 0.3 + 0.4 + 0.2 + 0.02 + 0.3 + 0.2 (recommendation also has 'migration' DB keyword +0.2) = 1.0 bounded
    assert score == 1.0
    assert "environment is production" in reason
    assert "severity is critical" in reason
    assert "security/auth concerns" in reason
    assert "critical destructive action" in reason

def test_approval_policy_enforcement(test_client, monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")
    
    # Create an incident and diagnostic run
    # 1. Low risk in dev -> approval_required should be False
    incident_resp = test_client.post("/v1/incidents", json={
        "project_key": "test-app",
        "source_system": "monitor",
        "environment": "development",
        "kind": "frontend",
        "severity": "LOW",
        "error_message": "traceback warning",
        "occurred_at": "2026-06-04T12:00:00Z"
    })
    inc_id = incident_resp.json()["id"]

    # Start diagnostic
    diag_start = test_client.post(f"/v1/incidents/{inc_id}/diagnostics")
    diag_id = diag_start.json()["diagnostic_id"]

    # Complete diagnostic with low risk mock recommendations
    from apps.bilgeapi.repositories.memory import memory_repositories
    memory_repositories.diagnostics[diag_id].status = DiagnosticStatus.COMPLETED
    memory_repositories.diagnostics[diag_id].confidence = 1.0
    memory_repositories.diagnostics[diag_id].recommendations = [{"description": "Minor style tweak"}]

    # Create repair request
    resp = test_client.post(f"/v1/diagnostics/{diag_id}/repair-requests?requested_by=operator")
    assert resp.status_code == 201
    data = resp.json()
    assert data["approval_required"] is False
    assert data["approval_status"] == "APPROVED"
    assert data["approved_by"] == "system"

def test_approval_policy_forces_production(test_client, monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")
    
    # 2. Production environment -> approval_required must be True regardless of low risk score
    incident_resp = test_client.post("/v1/incidents", json={
        "project_key": "test-app",
        "source_system": "monitor",
        "environment": "production",
        "kind": "frontend",
        "severity": "LOW",
        "error_message": "minor bug",
        "occurred_at": "2026-06-04T12:00:00Z"
    })
    inc_id = incident_resp.json()["id"]

    diag_start = test_client.post(f"/v1/incidents/{inc_id}/diagnostics")
    diag_id = diag_start.json()["diagnostic_id"]

    memory_repositories = get_memory_repos()
    memory_repositories.diagnostics[diag_id].status = DiagnosticStatus.COMPLETED
    memory_repositories.diagnostics[diag_id].confidence = 1.0
    memory_repositories.diagnostics[diag_id].recommendations = [{"description": "minor change"}]

    resp = test_client.post(f"/v1/diagnostics/{diag_id}/repair-requests?requested_by=operator")
    assert resp.status_code == 201
    assert resp.json()["approval_required"] is True
    assert resp.json()["approval_status"] == "PENDING"

def test_approval_policy_forces_sensitivity(test_client, monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")

    # 3. Development but contains database keyword -> approval_required must be True
    incident_resp = test_client.post("/v1/incidents", json={
        "project_key": "test-app",
        "source_system": "monitor",
        "environment": "development",
        "kind": "frontend",
        "severity": "LOW",
        "error_message": "db error",
        "occurred_at": "2026-06-04T12:00:00Z"
    })
    inc_id = incident_resp.json()["id"]

    diag_start = test_client.post(f"/v1/incidents/{inc_id}/diagnostics")
    diag_id = diag_start.json()["diagnostic_id"]

    memory_repositories = get_memory_repos()
    memory_repositories.diagnostics[diag_id].status = DiagnosticStatus.COMPLETED
    memory_repositories.diagnostics[diag_id].confidence = 1.0
    memory_repositories.diagnostics[diag_id].recommendations = [{"description": "Run postgres query"}]

    resp = test_client.post(f"/v1/diagnostics/{diag_id}/repair-requests?requested_by=operator")
    assert resp.status_code == 201
    assert resp.json()["approval_required"] is True
    assert resp.json()["approval_status"] == "PENDING"

def test_admin_approve_and_reject_flow(monkeypatch, test_client_real_auth):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator"])
    
    # 1. Create a request requiring approval
    incident_resp = test_client_real_auth.post("/v1/incidents", json={
        "project_key": "test-app",
        "source_system": "monitor",
        "environment": "production",
        "kind": "frontend",
        "severity": "HIGH",
        "error_message": "db error",
        "occurred_at": "2026-06-04T12:00:00Z"
    }, headers={"X-API-Key": "admin_key"})
    inc_id = incident_resp.json()["id"]

    diag_start = test_client_real_auth.post(f"/v1/incidents/{inc_id}/diagnostics", headers={"X-API-Key": "admin_key"})
    diag_id = diag_start.json()["diagnostic_id"]

    memory_repositories = get_memory_repos()
    memory_repositories.diagnostics[diag_id].status = DiagnosticStatus.COMPLETED
    memory_repositories.diagnostics[diag_id].confidence = 0.90
    memory_repositories.diagnostics[diag_id].recommendations = [{"description": "db restart"}]

    req_resp = test_client_real_auth.post(f"/v1/diagnostics/{diag_id}/repair-requests", headers={"X-API-Key": "op_key"})
    assert req_resp.status_code == 201
    rep_id = req_resp.json()["id"]

    # 2. Operator attempt to approve -> 403 Forbidden
    op_app = test_client_real_auth.post(f"/v1/repair-requests/{rep_id}/approve", headers={"X-API-Key": "op_key"})
    assert op_app.status_code == 403

    # 3. Admin rejects first (should work, but we'll approve first, or check state changes)
    # Let's create a separate request to reject
    req_resp2 = test_client_real_auth.post(f"/v1/diagnostics/{diag_id}/repair-requests", headers={"X-API-Key": "op_key"})
    rep_id_reject = req_resp2.json()["id"]

    admin_rej = test_client_real_auth.post(f"/v1/repair-requests/{rep_id_reject}/reject", json={"rejection_reason": "Too risky"}, headers={"X-API-Key": "admin_key"})
    assert admin_rej.status_code == 200
    assert admin_rej.json()["approval_status"] == "REJECTED"
    assert admin_rej.json()["rejection_reason"] == "Too risky"
    assert admin_rej.json()["rejected_at"] is not None

    # 4. Admin approves original request -> 200 OK
    admin_app = test_client_real_auth.post(f"/v1/repair-requests/{rep_id}/approve", headers={"X-API-Key": "admin_key"})
    assert admin_app.status_code == 200
    assert admin_app.json()["approval_status"] == "APPROVED"
    assert admin_app.json()["approved_by"].startswith("api_key_")
    assert "admin_key" not in admin_app.json()["approved_by"]
    assert admin_app.json()["approved_at"] is not None

def test_dispatch_constraints(monkeypatch, test_client_real_auth):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator"])
    monkeypatch.setattr(settings, "BILGEAPI_WEBHOOK_URL", "https://localhost:8080")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", True)

    # Mock dispatcher calls
    async def mock_post(*args, **kwargs):
        import httpx
        return httpx.Response(200, content=b"{}")
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    incident_resp = test_client_real_auth.post("/v1/incidents", json={
        "project_key": "test-app",
        "source_system": "monitor",
        "environment": "production",
        "kind": "frontend",
        "severity": "HIGH",
        "error_message": "db error",
        "occurred_at": "2026-06-04T12:00:00Z"
    }, headers={"X-API-Key": "admin_key"})
    inc_id = incident_resp.json()["id"]

    diag_start = test_client_real_auth.post(f"/v1/incidents/{inc_id}/diagnostics", headers={"X-API-Key": "admin_key"})
    diag_id = diag_start.json()["diagnostic_id"]

    memory_repositories = get_memory_repos()
    memory_repositories.diagnostics[diag_id].status = DiagnosticStatus.COMPLETED
    memory_repositories.diagnostics[diag_id].confidence = 0.90
    memory_repositories.diagnostics[diag_id].recommendations = [{"description": "db restart"}]

    req_resp = test_client_real_auth.post(f"/v1/diagnostics/{diag_id}/repair-requests", headers={"X-API-Key": "op_key"})
    rep_id = req_resp.json()["id"]

    # 1. Attempt dispatch before approval -> 400 Bad Request
    disp_resp = test_client_real_auth.post(f"/v1/repair-requests/{rep_id}/dispatch", headers={"X-API-Key": "op_key"})
    assert disp_resp.status_code == 400
    assert "unapproved" in disp_resp.json()["detail"].lower()

    # 2. Approve
    test_client_real_auth.post(f"/v1/repair-requests/{rep_id}/approve", headers={"X-API-Key": "admin_key"})

    # 3. Attempt dispatch after approval -> 200 OK
    disp_resp = test_client_real_auth.post(f"/v1/repair-requests/{rep_id}/dispatch", headers={"X-API-Key": "op_key"})
    assert disp_resp.status_code == 200

def test_direct_patch_prevention():
    # Verify no source code patches or dynamic file changes are present in services/routers
    import os
    import sys
    # Verify no execution wrapper tools were added to services
    assert not os.path.exists("apps/bilgeapi/services/execute.py")
    assert not os.path.exists("apps/bilgeapi/services/patcher.py")

def test_audit_chain(monkeypatch, test_client_real_auth):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin"])
    monkeypatch.setattr(settings, "BILGEAPI_WEBHOOK_URL", "https://localhost:8080")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", True)

    async def mock_post(*args, **kwargs):
        import httpx
        return httpx.Response(200, content=b"{}")
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    incident_resp = test_client_real_auth.post("/v1/incidents", json={
        "project_key": "test-app",
        "source_system": "monitor",
        "environment": "production",
        "kind": "frontend",
        "severity": "HIGH",
        "error_message": "db error",
        "occurred_at": "2026-06-04T12:00:00Z"
    }, headers={"X-API-Key": "admin_key"})
    inc_id = incident_resp.json()["id"]

    diag_start = test_client_real_auth.post(f"/v1/incidents/{inc_id}/diagnostics", headers={"X-API-Key": "admin_key"})
    diag_id = diag_start.json()["diagnostic_id"]

    memory_repositories = get_memory_repos()
    memory_repositories.diagnostics[diag_id].status = DiagnosticStatus.COMPLETED
    memory_repositories.diagnostics[diag_id].confidence = 0.90
    memory_repositories.diagnostics[diag_id].recommendations = [{"description": "db restart"}]

    # 1. Create -> REPAIR_REQUEST_CREATED and REPAIR_RISK_SCORED
    req_resp = test_client_real_auth.post(f"/v1/diagnostics/{diag_id}/repair-requests", headers={"X-API-Key": "admin_key"})
    rep_id = req_resp.json()["id"]

    # 2. Approve -> REPAIR_APPROVED
    test_client_real_auth.post(f"/v1/repair-requests/{rep_id}/approve", headers={"X-API-Key": "admin_key"})

    # 3. Dispatch -> REPAIR_DISPATCH_REQUESTED
    test_client_real_auth.post(f"/v1/repair-requests/{rep_id}/dispatch", headers={"X-API-Key": "admin_key"})

    # Check recent audits
    audit_resp = test_client_real_auth.get("/v1/audit-events", headers={"X-API-Key": "admin_key"})
    assert audit_resp.status_code == 200
    events = [e["event_type"] for e in audit_resp.json()]
    
    assert "REPAIR_REQUEST_CREATED" in events
    assert "REPAIR_RISK_SCORED" in events
    assert "REPAIR_APPROVED" in events
    assert "REPAIR_DISPATCH_REQUESTED" in events

# Utility helper
def get_memory_repos():
    from apps.bilgeapi.repositories.memory import memory_repositories
    return memory_repositories
