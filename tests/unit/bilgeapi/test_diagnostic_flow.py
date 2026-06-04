import pytest
import asyncio
from datetime import datetime, timezone

VALID_INCIDENT_PAYLOAD = {
    "project_key": "payment-platform",
    "source_system": "backend-api",
    "environment": "production",
    "kind": "backend",
    "severity": "CRITICAL",
    "error_message": "Connection timeout on port 5432",
    "occurred_at": "2026-06-04T13:20:00Z",
    "correlation_id": "req_abc123"
}

def test_trigger_diagnostic_not_found(test_client):
    response = test_client.post("/v1/incidents/nonexistent_inc_id/diagnostics")
    assert response.status_code == 404

def test_trigger_and_poll_diagnostic_flow(test_client):
    # 1. Ingest incident
    inc_resp = test_client.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD)
    assert inc_resp.status_code == 201
    inc_id = inc_resp.json()["id"]

    # 2. Trigger diagnostic run
    diag_resp = test_client.post(f"/v1/incidents/{inc_id}/diagnostics")
    assert diag_resp.status_code == 202
    start_data = diag_resp.json()
    assert "diagnostic_id" in start_data
    assert start_data["status"] == "QUEUED"
    assert start_data["next_action"] == "CHECK_DIAGNOSTIC_STATUS"
    diag_id = start_data["diagnostic_id"]

    # 3. Retrieve status immediately -> should be QUEUED or RUNNING
    poll_resp = test_client.get(f"/v1/diagnostics/{diag_id}")
    assert poll_resp.status_code == 200
    assert poll_resp.json()["status"] in ("QUEUED", "RUNNING")

    # 4. Wait for async background task completion (mock agent sleeps for 0.1s internally)
    # We sleep a bit longer in test context to guarantee execution complete
    import time
    time.sleep(0.3)

    # 5. Retrieve status again -> should be COMPLETED
    poll_resp = test_client.get(f"/v1/diagnostics/{diag_id}")
    assert poll_resp.status_code == 200
    res_data = poll_resp.json()
    assert res_data["status"] == "COMPLETED"
    assert "timeout" in res_data["summary"].lower()
    assert res_data["confidence"] == 0.85
    assert len(res_data["findings"]) >= 1
    assert len(res_data["recommendations"]) >= 1

    # 6. List all diagnostics
    list_resp = test_client.get("/v1/diagnostics")
    assert list_resp.status_code == 200
    all_runs = list_resp.json()
    assert any(x["diagnostic_id"] == diag_id for x in all_runs)

    # 7. Check audit trail for lifecycle transitions
    audit_resp = test_client.get("/v1/audit-events")
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    
    event_types = [e["event_type"] for e in events if e["entity_id"] == diag_id]
    assert "DIAGNOSTIC_QUEUED" in event_types
    assert "DIAGNOSTIC_RUNNING" in event_types
    assert "DIAGNOSTIC_COMPLETED" in event_types

def test_diagnostic_failed_lifecycle(monkeypatch, test_client):
    from apps.bilgeapi.adapters.mock_agent import MockAgentAdapter
    
    # Patch run_diagnostic to raise an exception
    async def mock_raise(*args, **kwargs):
        raise ValueError("Simulated diagnostic failure")
    monkeypatch.setattr(MockAgentAdapter, "run_diagnostic", mock_raise)

    # Ingest incident
    inc_resp = test_client.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD)
    assert inc_resp.status_code == 201
    inc_id = inc_resp.json()["id"]

    # Trigger diagnostic
    diag_resp = test_client.post(f"/v1/incidents/{inc_id}/diagnostics")
    assert diag_resp.status_code == 202
    diag_id = diag_resp.json()["diagnostic_id"]

    # Wait for async background execution to fail
    import time
    time.sleep(0.3)

    # Verify status is FAILED
    poll_resp = test_client.get(f"/v1/diagnostics/{diag_id}")
    assert poll_resp.status_code == 200
    assert poll_resp.json()["status"] == "FAILED"

    # Verify audit event log
    audit_resp = test_client.get("/v1/audit-events")
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    event_types = [e["event_type"] for e in events if e["entity_id"] == diag_id]
    assert "DIAGNOSTIC_FAILED" in event_types
