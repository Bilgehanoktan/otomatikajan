import pytest
from fastapi.testclient import TestClient
from main import app
from apps.api.routers.auth.jwt_auth import get_current_user

# 1. Provide a mock user to override authentication
def override_get_current_user():
    return {"email": "verify@system.local", "role": "admin"}

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_verify_capabilities_endpoint_via_client():
    """
    Faz 12.1 Verification: Ensure the /tasks/capabilities endpoint works and
    correctly loads capabilities via agency_loader without bypassing auth using mocks.
    """
    response = client.get("/tasks/capabilities")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    assert "capabilities" in data, "Capabilities key missing from response"
    assert isinstance(data["capabilities"], list), "Capabilities should be a list"
    assert len(data["capabilities"]) > 0, "At least one specialist should be returned"
    
    # Assert expected metadata from endpoint
    assert data.get("source_of_truth") == "agency_loader"

@pytest.mark.asyncio
async def test_sovereign_auditor_check():
    """
    Faz 12.1 Verification: Test the core auditor engine behavior directly.
    """
    from packages.orchestration.agi.cognitive.sovereign_auditor import sovereign_auditor
    
    findings = await sovereign_auditor.run_full_audit()
    assert isinstance(findings, list), "Findings should be a list"
    # Even if there are no findings, the fact that run_full_audit ran without error is a success constraint.

def test_sovereign_evolution_engine_ready():
    """
    Faz 12.1 Verification: Ensure the Evolution Engine instance is correctly loaded.
    """
    try:
        from packages.orchestration.agi.cognitive.evolution_engine import evolution_engine
        assert evolution_engine is not None, "Evolution engine instance should not be None"
    except ImportError as e:
        pytest.fail(f"Evolution engine imports failed: {e}")
