import asyncio
import uuid
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex, SovereignGoal
from packages.orchestration.agi.task_governance import GovernedTask, GovernanceStatus
from packages.persistence.models import Project, ProjectStatus

async def test_long_horizon_resume_v37():
    print("\n--- Phase 37: Long-Horizon Execution Persistence Test ---")
    
    # 1. Mock Project and SubTasks
    mock_project_id = uuid.uuid4()
    
    # Completed SubTask
    st1 = SubTask(id=str(uuid.uuid4()), agent_id="architect", prompt="Task 1", status=TaskStatus.COMPLETED, result="Done", structured=MagicMock())
    # Not Completed SubTask
    st2 = SubTask(id=str(uuid.uuid4()), agent_id="backend_dev", prompt="Task 2", status=TaskStatus.PENDING, result="", structured=MagicMock())
    
    # Project with subtasks and context
    mock_project = Project(
        id=mock_project_id,
        title="Long Horizon Test",
        status=ProjectStatus.RUNNING,
        execution_context={"agi_subtasks": ["architect", "backend_dev"]},
        subtasks=[st1, st2]
    )

    # 2. Setup Cortex
    cortex = SovereignCortex()
    cortex._is_running = True # Bypass start()
    
    # Track execution
    executed_agents = []
    
    async def mock_nexus(st_obj, task_obj):
        print(f"[MOCK] Executing nexus for {st_obj.agent_id}")
        executed_agents.append(st_obj.agent_id)
        st_obj.status = ProjectStatus.COMPLETED
        return True

    cortex._execute_subtask_nexus = mock_nexus
    cortex._update_project_context = AsyncMock() # Skip real DB calls
    cortex.state_svc.save = MagicMock()

    # 3. Create ProjectTask (The internal runtime object)
    task = ProjectTask(
        id=str(mock_project_id),
        title=mock_project.title,
        status=ProjectStatus.RUNNING,
        execution_context={"agi_subtasks": ["architect", "backend_dev"]},
        subtasks=[st1, st2]
    )

    print(f"[TEST] Starting execution for project {mock_project_id}...")
    
    # In real code, _execute_task is called. 
    # We call it directly to verify resume logic.
    print(f"[TEST] Starting coordinate_goal for project {mock_project_id}...")
    
    # In real code, the loop is inside coordinate_goal.
    # To test the loop specifically, we can invoke the class method if we refactor,
    # or just mock the dependencies of coordinate_goal.
    
    # Let's mock coordinate_goal's prerequisites to test the loop logic
    cortex.motivation.recalibrate_state = AsyncMock(return_value=MagicMock(persistence_policy="test"))
    cortex.affective.get_current_mood = MagicMock(return_value="neutral")
    cortex._execute_dialectic_planning = AsyncMock(return_value=task)
    
    await cortex.coordinate_goal("Test Title", "Test Desc", project_id=str(mock_project_id))

    # 4. Verify results
    print(f"[TEST] Executed agents: {executed_agents}")
    
    # architech was COMPLETED, so it should be skipped. 
    # backend_dev was PENDING, so it should be executed.
    assert "architect" not in executed_agents, "ERROR: architect should have been skipped (already COMPLETED)"
    assert "backend_dev" in executed_agents, "ERROR: backend_dev should have been executed"
    
    print("[SUCCESS] Long-Horizon Persistence & Resume logic verified.")

if __name__ == "__main__":
    asyncio.run(test_long_horizon_resume_v37())
