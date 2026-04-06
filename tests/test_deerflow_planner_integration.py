import pytest
import asyncio
import json
import uuid
from unittest.mock import MagicMock, AsyncMock

from packages.persistence.models import Project, ProjectStatus, SubTask
from packages.persistence.repository import ProjectRepository, SubTaskRepository
from tasks.deerflow_tasks import run_deerflow_streaming_task

@pytest.mark.asyncio
async def test_deerflow_planner_subtask_extraction(mocker):
    # 1. Setup Mock DB Session
    mock_db = AsyncMock()
    # Mock AsyncSessionLocal to return our mock_db
    mocker.patch("tasks.deerflow_tasks.AsyncSessionLocal", return_value=mock_db)
    mock_db.__aenter__.return_value = mock_db
    
    # 2. Setup Project
    project_id = uuid.uuid4()
    mock_project = Project(
        id=project_id,
        title="Test Project",
        description="Test Description",
        status=ProjectStatus.PENDING
    )
    
    # Mock Repository calls
    mocker.patch("packages.persistence.repository.ProjectRepository.get", return_value=mock_project)
    mocker.patch("packages.persistence.repository.ProjectRepository.mark_started", return_value=None)
    mocker.patch("packages.persistence.repository.ProjectRepository.mark_completed", return_value=None)
    mocker.patch("packages.persistence.repository.TaskLogRepository.write", return_value=None)
    
    # 3. Mock Bridge Client
    mock_bridge = MagicMock()
    mocker.patch("tasks.deerflow_tasks.DeerFlowBridgeClient", return_value=mock_bridge)
    
    # Mock Streaming response
    test_plan_json = {
        "subtasks": [
            {"agent_id": "researcher", "prompt": "Investigate X"},
            {"agent_id": "coder", "prompt": "Implement Y"}
        ]
    }
    
    async def mock_stream(*args, **kwargs):
        # Event 1: Thought
        yield {"event": "thought", "data": "Planning system architecture..."}
        # Event 2: Final Answer with JSON
        yield {"event": "answer", "data": f"Here is the plan:\n```json\n{json.dumps(test_plan_json)}\n```"}

    mock_bridge.stream_run = mock_stream

    # 4. Mock SubTask Creation
    mock_bulk_create = mocker.patch("packages.persistence.repository.SubTaskRepository.bulk_create", return_value=[])

    # 5. Run the Task (Simulated Celery environment)
    # We call the inner function _execute logic by bypassing celery's delay()
    from tasks.deerflow_tasks import run_async
    
    # We need to mock the build_deerflow_prompt as well
    mocker.patch("core.deerflow_prompts.build_deerflow_prompt", return_value="System prompt")

    # The actual function is 'run_deerflow_streaming_task' which is a celery task
    # We want to test the internal _execute logic. 
    # Since _execute is local to run_deerflow_streaming_task, we might need a different approach 
    # if we want to test exactly that. But for now, we can run the whole task.
    
    # Mocking run_async to just await the coro
    async def mock_run_async(coro):
        return await coro
    mocker.patch("tasks.deerflow_tasks.run_async", side_effect=mock_run_async)

    result = await run_deerflow_streaming_task(
        db_project_id=str(project_id),
        title="Test Project",
        description="Test Description",
        deerflow_role="deerflow_plan"
    )

    # 6. Assertions
    assert result["status"] == "success"
    # Check if bulk_create was called with the correct subtasks
    mock_bulk_create.assert_called_once()
    args, _ = mock_bulk_create.call_args
    # args[0] is db, args[1] is project_id, args[2] is subtasks
    assert len(args[2]) == 2
    assert args[2][0]["agent_id"] == "researcher"
    print("\n[SUCCESS] DeerFlow Planner subtask extraction test passed!")

if __name__ == "__main__":
    # This part is for manual running
    import sys
    import pytest
    pytest.main([__file__, "-v", "-s"])
