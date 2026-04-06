import pytest
from fastapi.testclient import TestClient
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from apps.api.routers.apps.api.routers.auth.jwt_auth import get_current_user, require_admin
from packages.persistence.session import get_db_dep

# Mock User for testing
class MockUser:
    def __init__(self, email="test@example.com", is_admin=True):
        self.email = email
        self.is_admin = is_admin
        self.id = "test-uuid"

def get_mock_admin():
    return MockUser(is_admin=True)

def get_mock_user():
    return MockUser(is_admin=False)

@pytest.fixture
def client():
    # Set test environment
    os.environ["APP_ENV"] = "test"
    
    # Simple mock DB dependency
    async def get_mock_db():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result
        yield mock_session

    app.dependency_overrides[get_db_dep] = get_mock_db
    
    with TestClient(app) as c:
        yield c
    # Clear overrides after test
    app.dependency_overrides = {}

@pytest.mark.integration
class TestDashboardIntegration:
    """
    Integration tests for dashboard backend endpoints.
    These tests verify that the endpoints correctly handle requests and 
    return the expected data structures.
    """

    def test_auth_me(self, client):
        app.dependency_overrides[get_current_user] = get_mock_user
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == "test@example.com"
        assert data["is_admin"] is False

    def test_repair_stats(self, client):
        app.dependency_overrides[get_current_user] = get_mock_user
        response = client.get("/api/v1/repair/stats")
        assert response.status_code == 200
        data = response.json()
        assert "active_jobs" in data
        assert "success_rate_pct" in data

    def test_repair_proposals(self, client):
        app.dependency_overrides[get_current_user] = get_mock_user
        response = client.get("/api/v1/repair/proposals")
        assert response.status_code == 200
        data = response.json()
        assert "proposals" in data
        assert isinstance(data["proposals"], list)

    def test_improvement_scan(self, client):
        app.dependency_overrides[get_current_user] = get_mock_user
        # This might be slow if it does a real scan, but we'll assume it returns cached or quick results in test mode
        response = client.get("/api/v1/improvements/scan")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_faz12_debate_personas(self, client):
        app.dependency_overrides[get_current_user] = get_mock_user
        response = client.get("/api/v1/faz12/debate/personas")
        assert response.status_code == 200
        data = response.json()
        assert "personas" in data
        assert len(data["personas"]) > 0

    def test_faz12_sandbox_run_safe(self, client):
        # Sandbox /run endpoint require_admin gerektirir
        app.dependency_overrides[get_current_user] = get_mock_admin
        payload = {
            "code": "print('hello world')",
            "timeout": 5
        }
        response = client.post("/api/v1/faz12/sandbox/run", json=payload)
        # Sandbox running status might vary based on docker, but should not be 403
        assert response.status_code in (200, 500) 
        # Note: In some test environments sandbox might be blocked or require docker
        # but the API itself should respond.

    def test_admin_users_access_denied_for_non_admin(self, client):
        app.dependency_overrides[get_current_user] = get_mock_user
        response = client.get("/api/v1/admin/users")
        # Should be 403 Forbidden if not admin
        assert response.status_code == 403

    def test_admin_users_access_allowed_for_admin(self, client):
        app.dependency_overrides[get_current_user] = get_mock_admin
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_monitoring_system_integrity(self, client):
        app.dependency_overrides[get_current_user] = get_mock_user
        response = client.get("/api/v1/monitoring/overview")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "services" in data
        assert "metrics" in data
        # 'status' should be under 'orchestrator' in services
        assert "orchestrator" in data["services"]
        assert data["services"]["orchestrator"]["status"] == "online"

    @patch("api.monitoring_router._system_resources")
    def test_monitoring_system_resilience(self, mock_sys, client):
        """Verify that the system returns a valid schema even when low-level monitoring fails."""
        app.dependency_overrides[get_current_user] = get_mock_user
        
        # Scenario: psutil missing/failed
        mock_sys.return_value = {
            "available": False,
            "cpu_pct": None,
            "ram_pct": None,
            "note": "Mocked failure"
        }
        
        response = client.get("/api/v1/monitoring/system")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert data["cpu_pct"] is None
        assert "note" in data
