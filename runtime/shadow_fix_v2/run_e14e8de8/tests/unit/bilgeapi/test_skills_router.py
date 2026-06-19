import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.bilgeapi.services.skill_registry import SkillRegistryService
from apps.bilgeapi.schemas.skills import SkillMetadataResponse
from apps.bilgeapi.routers.deps import get_skill_registry

@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=SkillRegistryService)
    registry.initialized = True
    
    # Mock return list
    skill_1 = SkillMetadataResponse(
        name="test-skill-1",
        source="external-vendor",
        version="1.0.0",
        license="MIT",
        risk_level="low",
        allowed_use=["test"],
        forbidden_use=[],
        hash="hash1",
        enabled=True,
        description="Test description 1",
        category="General"
    )
    skill_2 = SkillMetadataResponse(
        name="test-skill-2",
        source="bilgeapi-custom",
        version="1.0.0",
        license="MIT",
        risk_level="high_value_policy",
        allowed_use=["test"],
        forbidden_use=[],
        hash="hash2",
        enabled=True,
        description="Test description 2",
        category="Review"
    )
    
    registry.list_skills.return_value = [skill_1, skill_2]
    
    def get_skill_side_effect(name):
        if name == "test-skill-1":
            return skill_1
        elif name == "test-skill-2":
            return skill_2
        else:
            raise ValueError(f"Skill {name} not found")
            
    registry.get_skill.side_effect = get_skill_side_effect
    return registry

@pytest.fixture
def app_with_mock_registry(mock_registry):
    from apps.bilgeapi.main import app
    # Override dependency and set state
    app.state.skill_registry = mock_registry
    app.dependency_overrides[get_skill_registry] = lambda: mock_registry
    yield app
    app.dependency_overrides.clear()

def test_list_skills_endpoint(app_with_mock_registry):
    client = TestClient(app_with_mock_registry)
    response = client.get("/v1/catalog/skills")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "test-skill-1"
    assert data[1]["name"] == "test-skill-2"
    assert data[1]["risk_level"] == "high_value_policy"

def test_get_skill_detail_endpoint(app_with_mock_registry):
    client = TestClient(app_with_mock_registry)
    
    # Happy path
    response = client.get("/v1/catalog/skills/test-skill-1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-skill-1"
    assert data["category"] == "General"

    # Skill not found (404)
    response = client.get("/v1/catalog/skills/unknown-skill")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_registry_error_returns_500(app_with_mock_registry, mock_registry):
    client = TestClient(app_with_mock_registry)
    mock_registry.list_skills.side_effect = RuntimeError("Database offline or corrupt registry")
    
    response = client.get("/v1/catalog/skills")
    assert response.status_code == 500
    assert "Database offline" in response.json()["detail"]
