import sys
import os
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# Ana dizini path'e ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDeerFlowIntegration(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.mock_user = MagicMock()
        self.mock_user.id = "test-user-id"

    async def test_bridge_client_run(self):
        """Bridge client'ın doğru adrese istek attığını doğrula."""
        from integrations.deerflow_bridge import DeerFlowBridgeClient
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient', autospec=True) as mock_client_class:
            mock_client = mock_client_class.return_value.__aenter__.return_value
            mock_client.post = AsyncMock(return_value=mock_response)
            
            client = DeerFlowBridgeClient(base_url="http://test-bridge:8010")
            result = await client.run(thread_id="t1", prompt="hello world")
            
            self.assertEqual(result["result"], "success")
            mock_client.post.assert_called_once()
            
            # URL kontrolü
            call_url = mock_client.post.call_args[0][0]
            self.assertEqual(call_url, "http://test-bridge:8010/run")

    async def test_routing_to_deerflow(self):
        """API'nin 'deerflow' ajanını doğru Celery görevine yönlendirdiğini doğrula."""
        from api.task_write_router import create_task
        from api._task_shared import TaskCreateRequest
        
        # Mocks for all internal components
        mock_db = MagicMock()
        mock_db.commit = AsyncMock()
        mock_project = MagicMock()
        mock_project.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_project.created_at = datetime.now()
        mock_project.started_at = None
        mock_project.completed_at = None
        mock_project.deadline = None
        mock_project.cancelled_at = None
        mock_project.title = "test"
        mock_project.description = "test"
        mock_project.status = "pending"
        
        mock_job = MagicMock()
        mock_job.id = "job-id"

        # Patching EVERYTHING used inside create_task
        with patch('db.session.AsyncSessionLocal') as mock_session_class, \
             patch('db.repository.ProjectRepository', autospec=True) as mock_repo, \
             patch('db.repository.TaskLogRepository', autospec=True) as mock_log_repo, \
             patch('core.job_queue.job_queue.enqueue', new_callable=AsyncMock) as mock_enqueue, \
             patch('core.events.event_bus.emit', new_callable=AsyncMock) as mock_emit:
            
            # Setup session mock
            mock_session = mock_session_class.return_value
            mock_session.__aenter__.return_value = mock_db
            
            # Setup repo mocks
            mock_repo.create = AsyncMock(return_value=mock_project)
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
            
            await create_task(req, current_user=self.mock_user)
            
            # Routing check
            mock_enqueue.assert_called()
            task_name = mock_enqueue.call_args[0][0]
            self.assertEqual(task_name, "deerflow_run")
            
            # 2. Test: Normal görev
            mock_enqueue.reset_mock()
            req_normal = TaskCreateRequest(
                title="Normal Task",
                description="Run this normally",
                assigned_agent="engineer"
            )
            
            await create_task(req_normal, current_user=self.mock_user)
            task_name_normal = mock_enqueue.call_args[0][0]
            self.assertEqual(task_name_normal, "run_project")

if __name__ == "__main__":
    unittest.main()
