import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from apps.api.main import app
from apps.api.routers.auth.jwt_auth import _make_token
from datetime import timedelta

@pytest.fixture
def auth_token():
    return _make_token({"sub": "admin_test", "type": "access", "roles": ["admin"]}, timedelta(minutes=10))

def test_sentinel_service_status_online(auth_token):
    """VERIFICATION: Sentinel'in aktif servisleri 'online' olarak raporlamasını doğrula."""
    client = TestClient(app)
    
    with patch("psutil.process_iter") as mock_iter:
        m_proc = MagicMock()
        # Simulated psutil process with .info property returning cmdline
        # Simulated psutil process with .info property returning cmdline
        m_proc.info = {'cmdline': ["python", "-m", "apps.telegram_bot.polling"]}
        # Ensure the call with ['cmdline'] returns the mock process
        mock_iter.return_value = [m_proc]
        
        response = client.get("/monitoring/overview", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        
        assert "optional_services" in data
        assert data["optional_services"]["telegram_bot"] == "online"
        assert data["optional_services"]["watchdog"] == "offline"

def test_sentinel_service_status_offline(auth_token):
    """VERIFICATION: Sentinel'in eksik servisleri 'offline' olarak raporlamasını doğrula."""
    client = TestClient(app)
    
    with patch("psutil.process_iter") as mock_iter:
        mock_iter.return_value = []
        
        response = client.get("/monitoring/overview", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["optional_services"]["telegram_bot"] == "offline"
        assert data["optional_services"]["watchdog"] == "offline"
        assert data["optional_services"]["scheduler"] == "offline"
