import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from packages.skills.registry import skill_registry
from packages.skills.base import SkillRequest, SkillResult
from packages.persistence.models import SkillExecutionLog

@pytest.mark.asyncio
async def test_skill_execution_logging_persistence():
    """
    SkillRegistry.execute çağrıldığında SkillExecutionLog oluşturuluyor mu?
    """
    req = SkillRequest(
        task_type="test",
        title="Test Skill",
        description="Testing persistence",
        project_id=None
    )
    
    # Mock the internal adapter
    mock_adapter = MagicMock()
    mock_adapter.execute = AsyncMock(return_value=SkillResult(
        success=True, skill_id="test_skill", summary="Persistence verified"
    ))
    
    with patch.object(skill_registry, "get", return_value=mock_adapter):
        # Mock the DB session to avoid real DB dependency in unit level
        with patch("packages.skills.logger.get_db_session") as mock_session_cm:
            mock_session = MagicMock()
            mock_session_cm.return_value.__aenter__.return_value = mock_session
            
            res = await skill_registry.execute("test_skill", req)
            
            assert res.success
            assert res.summary == "Persistence verified"
            
            # Verify packages.persistence.add was called with SkillExecutionLog
            assert mock_session.add.called
            log_entry = mock_session.add.call_args[0][0]
            assert isinstance(log_entry, SkillExecutionLog)
            assert log_entry.skill_id == "test_skill"
            assert log_entry.success is True
            assert log_entry.summary == "Persistence verified"
            assert mock_session.commit.called
