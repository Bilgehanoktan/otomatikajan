import pytest
from fastapi.testclient import TestClient
from services.workflow_api.main import app

def test_queue_detailed_api_endpoint():
    """
    Verifies that the new /api/v1/health/queue-detailed endpoint
    successfully fetches active worker counts and in-process stats.
    """
    client = TestClient(app)
    response = client.get("/api/v1/health/queue-detailed")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "concurrency" in data
    assert "active_workers" in data
    assert "queue_size" in data
    assert "backend" in data
    assert "stats" in data
    
    assert data["backend"] in {"inprocess", "celery"}
