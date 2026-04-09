import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from apps.api.routers.task_write import create_task
from apps.api.support._task_shared import TaskCreateRequest
from core.orchestrator import Orchestrator
from packages.skills.base import SkillRequest

@pytest.mark.asyncio
async def test_tsk01_tsk05_create_task_adds_suggested_skills_to_payload():
    """TSK-01, TSK-05 — Task creation sırasında skill önerileri üretiliyor ve loglanıyor"""
    mock_user = MagicMock()
    mock_user.id = "user-123"
    
    req = TaskCreateRequest(
        title="Fix bug in router",
        description="Traceback in async flow",
        source="manual",
        priority="high"
    )
    
    # Mocking DB and Queue
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_job = MagicMock()
    mock_job.id = "job-456"
    
    with patch("packages.persistence.session.AsyncSessionLocal") as mock_session, \
         patch("packages.persistence.repository.ProjectRepository.create", new_callable=AsyncMock) as mock_p_create, \
         patch("packages.persistence.repository.TaskLogRepository.write", new_callable=AsyncMock) as mock_log_write, \
         patch("packages.orchestration.application.job_queue.job_queue.enqueue", new_callable=AsyncMock) as mock_enqueue, \
         patch("packages.persistence.repository.ProjectRepository.set_job_id", new_callable=AsyncMock), \
         patch("packages.persistence.repository.ProjectRepository.update_fields", new_callable=AsyncMock):
        
        mock_session.return_value.__aenter__.return_value = mock_db
        mock_p_create.return_value = MagicMock(id="550e8400-e29b-41d4-a716-446655440000")
        mock_enqueue.return_value = mock_job
        
        from apps.api.routers.task_write import create_task
        await create_task(req, current_user=mock_user)
        
        # Verify enqueue was called with suggested_skills
        assert mock_enqueue.called
        kwargs = mock_enqueue.call_args.kwargs
        assert "suggested_skills" in kwargs
        assert "debugging" in kwargs["suggested_skills"]
        
        # Verify Log was written with suggested_skills payload
        # The second call to write is the one with job_id and suggested_skills
        log_payloads = [call.kwargs.get("payload", {}) for call in mock_log_write.call_args_list]
        assert any("suggested_skills" in p for p in log_payloads)

@pytest.mark.asyncio
async def test_orc01_orc05_orchestrator_injects_skills_into_prompt():
    """ORC-01, ORC-05 — Orchestrator skill sonuçlarını prompt'a enjekte ediyor"""
    orch = Orchestrator()
    
    # Mock skill preflight to return something
    with patch.object(orch, "_run_skill_preflight", new_callable=AsyncMock) as mock_preflight:
        mock_preflight.return_value = "[DEBUGGING]: Analiz edildi"
        
        # We need to reach the point where shared_context is updated
        # _run_subtask is where it happens
        st = MagicMock()
        st.agent_id = "backend_dev"
        st.prompt = "Write code"
        st.id = "st-1"
        st.db_subtask_id = "db-st-1"
        
        # Mock agent execution to not trigger real LLM
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock()
        mock_agent.execute.return_value = MagicMock(raw_output='{"summary": "ok", "actions": []}')
        orch._agents["backend_dev"] = mock_agent
        
        # Mock other dependencies in _run_subtask
        with patch.object(orch, "_evaluate_risk_semantically", return_value="LOW"), \
             patch("core.orchestrator.output_parser.parse") as mock_parse, \
             patch.object(orch, "_check_quality", return_value=(0.9, MagicMock())), \
             patch("packages.persistence.session.AsyncSessionLocal"), \
             patch("packages.persistence.repository.SubTaskRepository.mark_done", new_callable=AsyncMock):
            
            mock_parse.return_value = MagicMock(summary="ok", agent_id="backend_dev")
            
            await orch._run_subtask(st, project_id="p-1")
            
            # Check if execute was called with enriched shared_context
            args, kwargs = mock_agent.execute.call_args
            context = kwargs.get("context", {})
            assert "--- Skill Destekleri ---" in context.get("shared_context", "")
            assert "[DEBUGGING]: Analiz edildi" in context.get("shared_context", "")
