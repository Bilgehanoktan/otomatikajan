import asyncio
import logging
import json
from unittest.mock import AsyncMock, patch, MagicMock
from core.agi.cognitive.sovereign_cortex import SovereignCortex
from core.agi.task_governance import SovereignGoal, GovernedTask, TaskStatus, TaskPlanner, GovernanceStatus

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("phase_39_verif")

async def test_sovereign_consensus_flow():
    _log.info("Starting Phase 39 Verification: Sovereign Consensus & Multi-Agent Coordination...")

    # 1. Initialize Planner and verify Risk Assessment
    planner = TaskPlanner()
    title = "Refactor Core Auth API"
    desc = "This task modifies the core authentication logic."
    
    _log.info("Scenario A: Verifying Autonomous Risk Assessment...")
    subtasks = planner.plan(title, desc)
    
    high_risk_tasks = [st for st in subtasks if st.consensus_required]
    if high_risk_tasks:
        _log.info(f"✅ SUCCESS: Detected {len(high_risk_tasks)} tasks requiring consensus.")
    else:
        _log.error("❌ FAILURE: No tasks marked for consensus despite high-risk keywords!")
        return

    # 2. Mock Consensus Manager and execution components
    cortex = SovereignCortex()
    await cortex.start()
    
    mock_consensus = {
        "consensus_score": 0.95,
        "hybrid_plan": "Consensus Plan: Security verified refactor.",
        "synthesis_logic": "Architect and Security agreement.",
        "points_of_agreement": ["Use JWT", "Enable MFA"],
        "residual_risks": []
    }

    # 3. Execution Simulation
    _log.info("Scenario B: Verifying Consensus Dialectic in Execution Loop...")
    
    # Mock velocity_engine to avoid actual tool use
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output_data = "Executed Consensus Plan."
    
    with patch("core.agi.cognitive.consensus_manager.consensus_manager.resolve", AsyncMock(return_value=mock_consensus)), \
         patch("core.agi.operational.velocity_engine.velocity_engine.simulate_and_execute", AsyncMock(return_value=mock_result)), \
         patch("core.agi.cognitive.sovereign_cortex.synaptic_cortex.save_episode"), \
         patch("core.agi.cognitive.synaptic_cortex.synaptic_cortex.save"), \
         patch("core.agi.learning.cognitive_mirror.cognitive_mirror.reflect"):
        
        # Test just the execute_subtask_nexus for one high-risk task
        test_task = high_risk_tasks[0]
        parent = SovereignGoal(id="p39", title=title, status=GovernanceStatus.RUNNING)
        parent.subtasks = subtasks
        
        await cortex._execute_subtask_nexus(test_task, parent)
        
        if test_task.consensus_score == 0.95 and "Consensus Plan" in test_task.prompt:
            _log.info("✅ SUCCESS: Dialectic Consensus flow executed and plan synthesized.")
        else:
            _log.error(f"❌ FAILURE: Consensus data not correctly applied. Score: {test_task.consensus_score}")
            return

    _log.info("Phase 39 Verification COMPLETED.")

if __name__ == "__main__":
    asyncio.run(test_sovereign_consensus_flow())
