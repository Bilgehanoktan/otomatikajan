import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from main import app
from auth.jwt_auth import _make_token
from datetime import timedelta
from unittest.mock import patch, MagicMock

@pytest.fixture
def auth_token():
    return _make_token({"sub": "admin_test", "type": "access", "roles": ["admin"]}, timedelta(minutes=10))

@pytest.mark.asyncio
async def test_skill_log_traceability_api(auth_token):
    """VERIFICATION: Skill loglarının data ve errors alanlarını doğru serileştirdiğini doğrula."""
    client = TestClient(app)
    
    mock_log = MagicMock()
    mock_log.id = uuid.uuid4()
    mock_log.project_id = uuid.uuid4()
    mock_log.agent_id = "test_agent"
    mock_log.skill_id = "test_skill"
    mock_log.success = True
    mock_log.summary = "Test summary"
    mock_log.data = {"input": "foo", "output": "bar"}
    mock_log.errors = None
    mock_log.duration_s = 1.2
    mock_log.created_at = datetime.now(timezone.utc)
    
    # Matching the API implementation: async with get_db_session() as db
    with patch("db.session.AsyncSessionLocal") as mock_session_ctx:
        mock_session = MagicMock()
        
        # Async context manager mock
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = MagicMock(return_value=mock_session)
        mock_ctx.__aexit__ = MagicMock(return_value=None)
        mock_session_ctx.return_value = mock_ctx
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_log]
        
        # Async execute
        async def mock_execute(*args, **kwargs):
            return mock_result
            
        mock_session.execute = mock_execute
        
        response = client.get("/skills/logs", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        logs = response.json()
        
        assert len(logs) == 1
        assert logs[0]["data"]["input"] == "foo"
        assert logs[0]["summary"] == "Test summary"
