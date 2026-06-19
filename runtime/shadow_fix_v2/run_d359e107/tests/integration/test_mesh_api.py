"""
Sovereign AGI — Phase 22
tests/integration/test_mesh_api.py
Integration tests for the newly created Mesh Observability and Actions APIs.
"""
import pytest
from fastapi.testclient import TestClient
from services.workflow_api.main import app

client = TestClient(app)

def test_get_mesh_status():
    """Verify that /api/v1/mesh/status returns the global mesh state."""
    response = client.get("/api/v1/mesh/status")
    assert response.status_code == 200
    data = response.json()
    assert "mesh_id" in data
    assert "regions" in data
    assert "quorum_maintained" in data

def test_get_mesh_drift():
    """Verify that /api/v1/mesh/drift returns security status."""
    response = client.get("/api/v1/mesh/drift")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "drifts" in data

def test_mesh_recalibrate_action():
    """Verify that the recalibrate action is accepted."""
    payload = {
        "operator_id": "test_admin",
        "reason": "Routine calibration check"
    }
    response = client.post("/api/v1/mesh/actions/recalibrate", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"

def test_mesh_freeze_action():
    """Verify that the global freeze action is accepted."""
    payload = {
        "operator_id": "test_admin",
        "reason": "Simulated emergency"
    }
    response = client.post("/api/v1/mesh/actions/freeze", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "FROZEN"
