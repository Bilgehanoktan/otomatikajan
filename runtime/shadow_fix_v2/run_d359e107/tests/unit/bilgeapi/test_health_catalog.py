import pytest

def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "bilgeapi"
    assert "version" in data
    assert "auth_mode" in data

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
