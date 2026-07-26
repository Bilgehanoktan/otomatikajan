import pytest

def test_root_index(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "bilgeapi"
    assert data["status"] == "ok"
    assert data["health_url"] == "/health"
    assert data["docs_url"] == "/docs"
    assert data["openapi_url"] == "/openapi.json"

def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "bilgeapi"
    
    # Detailed health
    response_ops = test_client.get("/v1/ops/health")
    assert response_ops.status_code == 200
    data_ops = response_ops.json()
    assert "version" in data_ops
    assert "auth_mode" in data_ops

def test_catalog(test_client):
    response = test_client.get("/v1/catalog")
    assert response.status_code == 200
    data = response.json()
    assert "diagnostics" in data
    assert "repair_dispatchers" in data
    
    # Verify mock_agent and webhook adapters exist in catalog descriptions
    diag_names = [d["name"] for d in data["diagnostics"]]
    dispatch_names = [w["name"] for w in data["repair_dispatchers"]]
    assert "mock_agent" in diag_names
    assert "webhook" in dispatch_names
