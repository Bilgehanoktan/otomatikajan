import os
import json
import pytest
import uuid
from fastapi.testclient import TestClient

from services.workflow_api.main import app
from services.auth.jwt_auth import get_current_identity

client = TestClient(app)


def test_get_suggestions_endpoint_no_audit_runs_triggers_ondemand(monkeypatch):
    # Override auth dependency by overriding get_current_identity
    mock_id = uuid.uuid4()
    app.dependency_overrides[get_current_identity] = lambda: {
        "id": mock_id,
        "type": "operator",
        "role": "OPERATOR"
    }

    # Mock AuditOrchestrator to return a dummy report on-demand
    dummy_report = {
        "audit_run_id": "AUD-TEST-ONDEMAND-123",
        "scanner": "create_audit_report",
        "status": "PASSED",
        "findings": [
            {
                "finding_id": "finding-test-1",
                "title": "On-demand Test Finding",
                "description": "This is a test finding",
                "category": "security",
                "severity": "CRITICAL"
            }
        ]
    }
    
    class MockAuditOrchestrator:
        def __init__(self, workspace_root=None):
            pass
        def execute_full_audit(self):
            return dummy_report

    import services.self_repair_audit.audit_orchestrator as audit_orch_mod
    monkeypatch.setattr(audit_orch_mod, "AuditOrchestrator", MockAuditOrchestrator)

    # Mock os.path.exists to pretend there are no audit run directories
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    try:
        response = client.get("/api/v1/ceo/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["audit_run_id"] == "AUD-TEST-ONDEMAND-123"
        assert len(data["findings"]) == 1
        assert data["findings"][0]["finding_id"] == "finding-test-1"
    finally:
        app.dependency_overrides.clear()


def test_get_suggestions_endpoint_with_existing_runs(monkeypatch):
    mock_id = uuid.uuid4()
    app.dependency_overrides[get_current_identity] = lambda: {
        "id": mock_id,
        "type": "operator",
        "role": "OPERATOR"
    }

    class MockOpen:
        def __init__(self, filename, *args, **kwargs):
            self.filename = filename
        def __enter__(self):
            content = {
                "findings": [
                    {
                        "finding_id": "finding-latest",
                        "title": "Latest Run Finding",
                        "category": "security",
                        "severity": "HIGH"
                    }
                ]
            }
            import io
            return io.StringIO(json.dumps(content))
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    import builtins
    original_open = builtins.open
    original_exists = os.path.exists
    original_isdir = os.path.isdir
    original_listdir = os.listdir

    def mock_exists(path):
        if "project_outputs" in str(path):
            return True
        return original_exists(path)

    def mock_isdir(path):
        if "project_outputs" in str(path):
            return True
        return original_isdir(path)

    def mock_listdir(path):
        if "project_outputs" in str(path):
            return ["AUD-20260519-100000", "AUD-20260519-120000", "AUD-20260519-110000"]
        return original_listdir(path)

    def mock_open(file, *args, **kwargs):
        if "AUD-20260519-120000" in str(file) and "classified_findings.json" in str(file):
            return MockOpen(file)
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(os.path, "exists", mock_exists)
    monkeypatch.setattr(os.path, "isdir", mock_isdir)
    monkeypatch.setattr(os, "listdir", mock_listdir)
    monkeypatch.setattr(builtins, "open", mock_open)

    try:
        response = client.get("/api/v1/ceo/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["audit_run_id"] == "AUD-20260519-120000"  # Verify alphabetical sort picks newest
        assert len(data["findings"]) == 1
        assert data["findings"][0]["finding_id"] == "finding-latest"
    finally:
        app.dependency_overrides.clear()


def test_get_suggestions_endpoint_unauthorized_returns_401():
    # Since we do not override get_current_identity, and no auth header is passed, the request is unauthorized
    response = client.get("/api/v1/ceo/suggestions")
    assert response.status_code == 401
