import pytest
import os
import json

VALID_INCIDENT = {
    "project_key": "payment-platform",
    "source_system": "backend-api",
    "environment": "production",
    "kind": "backend",
    "severity": "CRITICAL",
    "error_message": "Connection timeout on port 5432",
    "stack_trace": "Traceback...",
    "occurred_at": "2026-06-04T13:20:00Z",
    "correlation_id": "req_abc123",
    "tags": ["backend", "postgres", "timeout"],
    "metadata": {
        "region": "eu-central-1",
        "release": "2026.06.04"
    }
}

def test_create_incident_success(test_client):
    response = test_client.post("/v1/incidents", json=VALID_INCIDENT)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["project_key"] == "payment-platform"
    assert data["correlation_id"] == "req_abc123"

def test_create_incident_validation_error(test_client):
    # Missing required field: error_message
    invalid = VALID_INCIDENT.copy()
    del invalid["error_message"]
    response = test_client.post("/v1/incidents", json=invalid)
    assert response.status_code == 422

    # Invalid severity value
    invalid_sev = VALID_INCIDENT.copy()
    invalid_sev["severity"] = "SUPER_HIGH"
    response = test_client.post("/v1/incidents", json=invalid_sev)
    assert response.status_code == 422

def test_get_and_list_incidents(test_client):
    # Ingest one incident
    post_resp = test_client.post("/v1/incidents", json=VALID_INCIDENT)
    assert post_resp.status_code == 201
    inc_id = post_resp.json()["id"]

    # Get details
    get_resp = test_client.get(f"/v1/incidents/{inc_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == inc_id

    # List all
    list_resp = test_client.get("/v1/incidents")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert any(x["id"] == inc_id for x in items)

def test_auth_api_key_enforcement(monkeypatch, test_client):
    # Set auth mode to api_key
    from apps.bilgeapi.config import settings
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    
    # 1. Request without key -> 401/403
    response = test_client.post("/v1/incidents", json=VALID_INCIDENT)
    assert response.status_code in (401, 403)

    # 2. Request with invalid key -> 401/403
    headers = {"X-API-Key": "wrong_key"}
    response = test_client.post("/v1/incidents", json=VALID_INCIDENT, headers=headers)
    assert response.status_code in (401, 403)

    # 3. Request with valid key -> 201 Created
    headers = {"X-API-Key": "test_key_1"}
    response = test_client.post("/v1/incidents", json=VALID_INCIDENT, headers=headers)
    assert response.status_code == 201

def test_audit_trail_repository_and_log_file(test_client):
    # Clean audit.log if exists
    log_path = "apps/bilgeapi/audit.log"
    if os.path.exists(log_path):
        os.remove(log_path)

    # Ingest incident
    response = test_client.post("/v1/incidents", json=VALID_INCIDENT)
    assert response.status_code == 201
    inc_id = response.json()["id"]

    # Assert event added to audit repository
    audit_resp = test_client.get("/v1/audit-events")
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert len(events) >= 1
    
    # Filter for INCIDENT_CREATED
    inc_events = [e for e in events if e["event_type"] == "INCIDENT_CREATED"]
    assert len(inc_events) >= 1
    assert inc_events[0]["entity_id"] == inc_id
    assert inc_events[0]["correlation_id"] == "req_abc123"

    # Assert JSONL file exists and contains the event
    assert os.path.exists(log_path)
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) >= 1
    last_event = json.loads(lines[-1])
    assert last_event["event_type"] == "INCIDENT_CREATED"
    assert last_event["entity_id"] == inc_id
    assert last_event["correlation_id"] == "req_abc123"

def test_auth_jwt_enforcement(monkeypatch, test_client):
    from apps.bilgeapi.config import settings
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "jwt")
    
    # Missing auth header -> 401
    response = test_client.post("/v1/incidents", json=VALID_INCIDENT)
    assert response.status_code == 401
    
    # Invalid auth header -> 401
    headers = {"Authorization": "Basic credentials"}
    response = test_client.post("/v1/incidents", json=VALID_INCIDENT, headers=headers)
    assert response.status_code == 401
    
    # Valid auth header -> 201 Created
    import jwt
    from datetime import datetime, timezone, timedelta
    token = jwt.encode({
        "sub": "test_user",
        "role": "operator",
        "identity_type": "operator",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    }, settings.BILGEAPI_JWT_SECRET, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.post("/v1/incidents", json=VALID_INCIDENT, headers=headers)
    assert response.status_code == 201

def test_incident_not_found(test_client):
    response = test_client.get("/v1/incidents/nonexistent_id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"

def test_audit_redaction():
    from apps.bilgeapi.services.audit import redact_sensitive_data
    sample_data = {
        "api_key": "secret_key_123",
        "secret": "my_password",
        "token": "token_abc",
        "user": "normal_user",
        "nested": {
            "password": "unredacted_password",
            "safe_field": 42
        },
        "list_data": [
            {"secret_token": "abc_123"},
            "plain_text"
        ]
    }
    redacted = redact_sensitive_data(sample_data)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["secret"] == "[REDACTED]"
    assert redacted["token"] == "[REDACTED]"
    assert redacted["user"] == "normal_user"
    assert redacted["nested"]["password"] == "[REDACTED]"
    assert redacted["nested"]["safe_field"] == 42
    assert redacted["list_data"][0]["secret_token"] == "[REDACTED]"
    assert redacted["list_data"][1] == "plain_text"

def test_openapi_spec_contents():
    # Execute the export openapi script to make sure the file is up-to-date
    from scripts.export_bilgeapi_openapi import export_openapi
    export_openapi()
    
    # Load and assert
    schema_path = "docs/openapi/bilgeapi_openapi.json"
    assert os.path.exists(schema_path)
    with open(schema_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    
    assert "/v1/incidents" in spec["paths"]
    assert "IncidentCreate" in spec["components"]["schemas"]
    assert "IncidentResponse" in spec["components"]["schemas"]

@pytest.mark.asyncio
async def test_memory_repositories_coverage():
    from apps.bilgeapi.repositories.memory import (
        InMemoryDiagnosticRepository,
        InMemoryFindingRepository,
        InMemoryRecommendationRepository,
        InMemoryRepairRequestRepository,
        InMemoryWebhookDeliveryRepository
    )
    from apps.bilgeapi.schemas.diagnostic import DiagnosticStatus
    from apps.bilgeapi.schemas.repair import RepairRequestCreate, ApprovalStatus, DispatchStatus
    
    # 1. Diagnostic Repository
    diag_repo = InMemoryDiagnosticRepository()
    diag = await diag_repo.create("inc_123")
    assert diag.status == DiagnosticStatus.QUEUED
    
    diag_fetched = await diag_repo.get(diag.diagnostic_id)
    assert diag_fetched is not None
    assert diag_fetched.diagnostic_id == diag.diagnostic_id
    
    updated = await diag_repo.update(diag.diagnostic_id, DiagnosticStatus.COMPLETED, summary="Resolved")
    assert updated is not None
    assert updated.status == DiagnosticStatus.COMPLETED
    assert updated.summary == "Resolved"
    
    all_diags = await diag_repo.list_all()
    assert len(all_diags) == 1
    
    # Update nonexistent
    assert await diag_repo.update("nonexistent", DiagnosticStatus.COMPLETED) is None
    
    # 2. Finding & Recommendation Repositories
    find_repo = InMemoryFindingRepository()
    rec_repo = InMemoryRecommendationRepository()
    
    finding = await find_repo.create(diag.diagnostic_id, {"description": "port issue"})
    assert finding["diagnostic_id"] == diag.diagnostic_id
    
    rec = await rec_repo.create(diag.diagnostic_id, {"description": "restart"})
    assert rec["diagnostic_id"] == diag.diagnostic_id
    
    findings = await find_repo.list_by_diagnostic(diag.diagnostic_id)
    assert len(findings) == 1
    
    recs = await rec_repo.list_by_diagnostic(diag.diagnostic_id)
    assert len(recs) == 1
    
    # 3. Repair Request Repository
    repair_repo = InMemoryRepairRequestRepository()
    req = RepairRequestCreate(requested_by="admin", risk_score=0.1, risk_reason="minimal")
    rep_req = await repair_repo.create(diag.diagnostic_id, req)
    assert rep_req.requested_by == "admin"
    assert rep_req.approval_status == ApprovalStatus.PENDING
    
    rep_fetched = await repair_repo.get(rep_req.id)
    assert rep_fetched is not None
    assert rep_fetched.id == rep_req.id
    
    rep_updated = await repair_repo.update(rep_req.id, ApprovalStatus.APPROVED, DispatchStatus.DISPATCHED, approved_by="manager")
    assert rep_updated is not None
    assert rep_updated.approval_status == ApprovalStatus.APPROVED
    assert rep_updated.dispatch_status == DispatchStatus.DISPATCHED
    assert rep_updated.approved_by == "manager"
    
    all_reps = await repair_repo.list_all()
    assert len(all_reps) == 1
    
    # Update nonexistent
    assert await repair_repo.update("nonexistent", ApprovalStatus.APPROVED, DispatchStatus.DISPATCHED) is None
    
    # 4. Webhook Delivery Repository
    web_repo = InMemoryWebhookDeliveryRepository()
    await web_repo.log_delivery({"url": "https://example.com", "status": 200})

