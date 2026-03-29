import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from core.orchestrator import Orchestrator
from core.task_management import SubTask, TaskStatus
from skills.base import SkillResult

@pytest.mark.asyncio
async def test_e2e_01_bug_task_flow_triggers_debugging_skill():
    """E2E-01 — Bug task flow'unda debugging skill tetikleniyor mu?"""
    orch = Orchestrator()
    orch._is_running = True # Bypass start() for speed
    
    # Mocking agents and their registry
    mock_agent = MagicMock()
    mock_agent.execute = AsyncMock(return_value=MagicMock(raw_output="Fixed the bug."))
    orch._agents = {"backend_dev": mock_agent}
    orch.model_orch = MagicMock()
    
    # Subtask for a bug
    st = SubTask(
        id="st-123",
        agent_id="backend_dev",
        prompt="Fix the crash in the user login component.",
    )
    
    # Mock skill preflight results
    with patch("skills.router.SkillRouter.suggest", return_value=["optimization", "file_search"]), \
         patch("skills.registry.SkillRegistry.get") as mock_get:
        
        # Mock file_search result
        mock_file_skill = MagicMock()
        mock_file_skill.execute = AsyncMock(return_value=SkillResult(
            success=True, skill_id="file_search", summary="Found login.py"
        ))
        
        # Mock optimization result
        mock_opt_skill = MagicMock()
        mock_opt_skill.execute = AsyncMock(return_value=SkillResult(
            success=True, skill_id="optimization", summary="Applied cache patterns"
        ))
        
        def side_effect(sid):
            if sid == "file_search": return mock_file_skill
            if sid == "optimization": return mock_opt_skill
            return None
        mock_get.side_effect = side_effect
        
        # Run subtask in orchestrator
        await orch._run_subtask(st, project_id="proj-456")
        
        # Verify agent was called
        assert mock_agent.execute.called
        call_args = mock_agent.execute.call_args[1]
        context = call_args["context"]["shared_context"]
        
        # Verify skill insights were injected
        assert "OPTIMIZATION" in context
        assert "FILE_SEARCH" in context
        assert "Applied cache patterns" in context
        assert "Found login.py" in context

@pytest.mark.asyncio
async def test_e2e_02_skill_suggestion_during_run_subtask():
    """E2E-02 — Run subtask sırasında skill suggestion ve preflight entegrasyonu"""
    orch = Orchestrator()
    orch._is_running = True
    
    mock_agent = MagicMock()
    mock_agent.execute = AsyncMock(return_value=MagicMock(raw_output="Done."))
    orch._agents = {"qa_engineer": mock_agent}
    orch.model_orch = MagicMock()
    
    st = SubTask(
        id="st-789",
        agent_id="qa_engineer",
        prompt="Verify tests for performance module.",
    )
    
    # Real router but mocked registry
    with patch("skills.router.SkillRouter.suggest", return_value=["file_search"]):
        with patch("skills.registry.SkillRegistry.get") as mock_get:
            mock_skill = MagicMock()
            mock_skill.execute = AsyncMock(return_value=SkillResult(
                success=True, skill_id="file_search", summary="Scanned 5 files."
            ))
            mock_get.return_value = mock_skill
            
            await orch._run_subtask(st)
            
            # Check if skill results made it into the prompt
            context = mock_agent.execute.call_args[1]["context"]["shared_context"]
            assert "FILE_SEARCH" in context
            assert "Scanned 5 files." in context
