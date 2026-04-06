import asyncio
import uuid
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex
from packages.orchestration.agi.cognitive.goal_decomposer import SubTaskPlan
from packages.persistence.models import Project, ProjectStatus

async def test_long_horizon_persistence_v37():
    print("\n--- Phase 37: Long-Horizon Persistence Test ---")
    
    # 1. Mock Project with existing execution_context
    mock_project_id = uuid.uuid4()
    mock_project = Project(
        id=mock_project_id,
        title="Long Horizon Test Project",
        status=ProjectStatus.RUNNING,
        execution_context={
            "agi_subtasks": [
                {"agent_id": "architect", "prompt": "Task 1", "reasoning": "R1"},
                {"agent_id": "backend_dev", "prompt": "Task 2", "reasoning": "R2"},
                {"agent_id": "security", "prompt": "Task 3", "reasoning": "R3"}
            ],
            "agi_current_index": 1 # Should resume from Task 2
        }
    )

    # 2. Setup Cortex with the mock project
    cortex = SovereignCortex()
    
    # Mocking _execute_subtask_nexus to track calls
    cortex._execute_subtask_nexus = AsyncMock(return_value=True)
    cortex._update_project_context = AsyncMock()
    
    # Mocking the repository get call (if needed) or directly setting current_task
    # In real execution, current_task.project is loaded from DB.
    from packages.orchestration.agi.cognitive.sovereign_cortex import ProjectTask
    mock_task = ProjectTask(
        project_id=str(mock_project_id),
        goal="Simulated Long Horizon Goal",
        project=mock_project
    )
    cortex.current_task = mock_task

    print(f"[TEST] Resuming project {mock_project_id} from index 1...")
    
    # 3. Trigger execution
    # Note: execute() calls decompose() if subtasks are empty. 
    # We want to verify it skips decomposition if ctx exists.
    
    # For testing, we manually set the subtasks but emulate the logic
    # In the actual code, we need to ensure execute() loads from ctx.
    
    # Let's check if my recent change in sovereign_cortex.py handles the "empty subtasks but ctx exists" case.
    # Looking at my previous edit, I added:
    # ctx = asdict(self.current_task.project).get("execution_context", {}) or {}
    # if not self.subtasks and ctx.get("agi_subtasks"):
    #    self.subtasks = [SubTaskPlan(**st) for st in ctx["agi_subtasks"]]
    
    # WAIT: I didn't add the loading logic in the previous turn yet, only the saving.
    # I need to fix that first.
    
    print("[FAIL] Loading logic not yet implemented in sovereign_cortex.py")
    return False

if __name__ == "__main__":
    asyncio.run(test_long_horizon_persistence_v37())
