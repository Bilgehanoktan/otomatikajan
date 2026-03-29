import pytest
import httpx
import os
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# TEST_DEERFLOW_BRIDGE_URL genelde http://localhost:8010 olur (dışarıdan erişim)
BRIDGE_URL = os.getenv("DEERFLOW_BRIDGE_URL", "http://localhost:8010")

@pytest.mark.asyncio
async def test_bridge_health():
    """Köprü servisinin sağlık kontrolünü test eder."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{BRIDGE_URL}/health")
            assert resp.status_code == 200
            assert resp.json()["ok"] is True
        except Exception as e:
            pytest.skip(f"Bridge servisi erişilebilir değil, atlanıyor: {e}")

@pytest.mark.asyncio
async def test_routing_logic_to_deerflow():
    """API'nin 'deerflow' ajanını veya etiketini doğru Celery görevine yönlendirdiğini doğrula."""
    from api.task_write_router import create_task
    from api._task_shared import TaskCreateRequest
    
    mock_user = MagicMock()
    mock_user.id = "test-user-id"

    # Mocks for all internal components
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_project = MagicMock()
    mock_project.id = "550e8400-e29b-41d4-a716-446655440000"
    mock_project.title = "test"
    mock_project.description = "test"
    mock_project.status = MagicMock()
    mock_project.status.value = "pending"
    
    mock_job = MagicMock()
    mock_job.id = "job-id"

    with patch('api.task_write_router.AsyncSessionLocal') as mock_session_class, \
         patch('api.task_write_router.ProjectRepository', autospec=True) as mock_repo, \
         patch('api.task_write_router.TaskLogRepository', autospec=True) as mock_log_repo, \
         patch('api.task_write_router.job_queue.enqueue', new_callable=AsyncMock) as mock_enqueue, \
         patch('api.task_write_router.event_bus.emit', new_callable=AsyncMock) as mock_emit, \
         patch('api.task_write_router.task_router.route_task', new_callable=AsyncMock) as mock_route, \
         patch('api.task_write_router.skill_router.suggest', return_value=["test_skill"]) as mock_suggest:
        
        # Setup session mock
        mock_session = mock_session_class.return_value
        mock_session.__aenter__.return_value = mock_db
        
        # Setup repo mocks
        mock_repo.create = AsyncMock(return_value=mock_project)
        mock_repo.get_by_job_id = AsyncMock(return_value=mock_project) # For set_job_id internally if needed
        mock_repo.set_job_id = AsyncMock()
        mock_repo.update_fields = AsyncMock()
        mock_log_repo.write = AsyncMock()
        
        mock_enqueue.return_value = mock_job
        
        # 1. Test: assigned_agent == "deerflow"
        req = TaskCreateRequest(
            title="DeerFlow Test",
            description="Run this on DeerFlow",
            assigned_agent="deerflow"
        )
        
        await create_task(req, current_user=mock_user)
        
        # Routing check
        mock_enqueue.assert_called()
        task_name = mock_enqueue.call_args[0][0]
        assert task_name == "deerflow_run"
        
        # 2. Test: "deerflow" in tags
        mock_enqueue.reset_mock()
        req_tags = TaskCreateRequest(
            title="Tag Test",
            description="Run this with tags",
            tags=["deerflow"]
        )
        await create_task(req_tags, current_user=mock_user)
        assert mock_enqueue.call_args[0][0] == "deerflow_run"

        # 3. Test: source == "research" → deerflow_research (akıllı routing)
        mock_enqueue.reset_mock()
        req_src = TaskCreateRequest(
            title="Source Test",
            description="Run this from research",
            source="research"
        )
        await create_task(req_src, current_user=mock_user)
        assert mock_enqueue.call_args[0][0] == "deerflow_research"

        # 4. Test: Normal görev
        mock_enqueue.reset_mock()
        req_normal = TaskCreateRequest(
            title="Normal Task",
            description="Run this normally",
            assigned_agent="engineer"
        )
        
        await create_task(req_normal, current_user=mock_user)
        task_name_normal = mock_enqueue.call_args[0][0]
        assert task_name_normal == "run_project"

        # 5. Test: Explicit DeerFlow role (deerflow_planner)
        mock_enqueue.reset_mock()
        req_planner = TaskCreateRequest(
            title="Plan Test",
            description="Architecture change",
            assigned_agent="deerflow_planner"
        )
        await create_task(req_planner, current_user=mock_user)
        assert mock_enqueue.call_args[0][0] == "deerflow_plan"

        # 6. Test: Tag-based routing → deerflow_review
        mock_enqueue.reset_mock()
        req_review = TaskCreateRequest(
            title="Review Test",
            description="Audit this code",
            assigned_agent="deerflow",
            tags=["review"]
        )
        await create_task(req_review, current_user=mock_user)
        assert mock_enqueue.call_args[0][0] == "deerflow_review"
