import asyncio
import uuid
import logging
import json
from datetime import datetime, timezone
from dataclasses import asdict
from core.agi.cognitive.sovereign_cortex import sovereign_cortex
from core.agi.task_governance import SovereignGoal, GovernedTask, GovernanceStatus
from core.agi.operational.velocity_engine import velocity_engine
from unittest.mock import AsyncMock, patch, MagicMock

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("phase_36_verif")

async def verify_phase_36():
    _log.info("Starting Phase 36 Verification: Cognitive Continuity...")

    # 1. Setup Mock Project with Initial Shared State
    task_id = f"test-goal-{uuid.uuid4().hex[:6]}"
    project = SovereignGoal(
        id=task_id,
        title="Phase 36 Continuity Test",
        execution_context={"shared_state": {"initial_key": "initial_value"}}
    )
    
    subtask = GovernedTask(
        id="st1",
        agent_id="backend_dev",
        prompt="Test prompt"
    )
    project.subtasks = [subtask]

    _log.info(f"Initial Shared State: {project.get_shared_state()}")

    # 2. Mock VelocityEngine to check injection and simulate state update
    mock_result = AsyncMock()
    mock_result.success = True
    # Agent output contains a STATE_UPDATE block
    mock_result.output_data = (
        "Execution successful.\n"
        "[STATE_UPDATE]\n"
        '{"new_variable": "new_value", "updated_key": "overwritten"}'
    )
    mock_result.errors = []

    with patch.object(velocity_engine, "simulate_and_execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_result
        
        # Execute nexus
        await sovereign_cortex._execute_subtask_nexus(subtask, project)
        
        # Check Injection
        args, kwargs = mock_exec.call_args
        injected_context = kwargs.get("context", {})
        injected_state = injected_context.get("shared_state", {})
        
        if injected_state.get("initial_key") == "initial_value":
            _log.info("✅ SUCCESS: Shared state correctly injected into SubTask context.")
        else:
            _log.error(f"❌ FAILURE: Core state injection failed. Found: {injected_state}")

        # Check Extraction
        final_state = project.get_shared_state()
        if final_state.get("new_variable") == "new_value" and final_state.get("updated_key") == "overwritten":
            _log.info(f"✅ SUCCESS: Shared state correctly updated from agent output: {final_state}")
        else:
            _log.error(f"❌ FAILURE: State extraction failed. Current state: {final_state}")

    # 3. Test Metacognition API (Mocking DB)
    _log.info("Testing Metacognition API endpoint...")
    from api.monitoring_router import agi_metacognition_stats
    
    # Mocking DB chain: await db.execute() -> result.scalars().all()
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_scalars = MagicMock()
    
    # scalars().all() needs to return a list of objects with metadata_
    class MockRecord:
        def __init__(self):
            self.created_at = datetime.now(timezone.utc)
            self.body = "Mock lesson"
            self.metadata_ = {"metacognitive_score": 0.95}
            
    mock_scalars.all.return_value = [MockRecord()]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch("db.session.AsyncSessionLocal", return_value=mock_db), \
         patch("auth.jwt_auth.get_current_user"):
        
        try:
            # Pass limit explicitly because we are calling it outside FastAPI context
            resp = await agi_metacognition_stats(limit=50)
            if "average_metacognitive_confidence" in resp:
                _log.info(f"✅ SUCCESS: Metacognition API functional. Avg Confidence: {resp['average_metacognitive_confidence']}")
            else:
                _log.error(f"❌ FAILURE: API response missing keys: {resp}")
        except Exception as e:
            _log.error(f"❌ Metacognition API test failed: {e}")
            import traceback
            _log.error(traceback.format_exc())

    _log.info("Phase 36 Verification COMPLETED.")

if __name__ == "__main__":
    asyncio.run(verify_phase_36())
