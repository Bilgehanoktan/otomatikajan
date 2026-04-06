import asyncio
import uuid
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from packages.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex, sovereign_cortex
from packages.orchestration.agi.cognitive.goal_decomposer import GoalDecomposer, goal_decomposer
from packages.orchestration.agi.cognitive.consensus_manager import ConsensusManager, consensus_manager
from packages.orchestration.agi.cognitive.red_team_agent import red_team
from packages.orchestration.agi.task_governance import ProjectTask, SubTask, TaskStatus
from packages.orchestration.agi.schemas import PlanProposal

async def test_consensus_refinement():
    print("\n--- [TEST] Consensus Governance Refinement ---")
    mock_orch = AsyncMock()
    # First response: something that fails governance
    # Second response: a refined plan
    mock_orch.complete_task.side_effect = [
        MagicMock(content='{"consensus_score": 0.8, "hybrid_plan": "rm -rf /", "synthesis_logic": "aggressive"}'),
        MagicMock(content='{"consensus_score": 0.9, "hybrid_plan": "safe_delete()", "synthesis_logic": "safe"}')
    ]
    
    mock_watchdog = AsyncMock()
    # Mock a violation for the first plan
    mock_violation = MagicMock(description="Kritik dosya silme engellendi")
    mock_watchdog.predict_violations.side_effect = [[mock_violation], []]

    # [FIX] Mock red_team - Adverse audit needs to pass
    mock_red = AsyncMock()
    mock_red.attack_plan.return_value = MagicMock(threat_score=0.1, vulnerabilities=[])
    
    with patch("packages.orchestration.agi.governance.watchdog.governance_watchdog", mock_watchdog), \
         patch("packages.orchestration.agi.cognitive.consensus_manager.red_team", mock_red):
        consensus_manager.model_orch = mock_orch
        proposals = [
            PlanProposal(agent_id="test", content="rm -rf /", confidence=0.5),
            PlanProposal(agent_id="security", content="ls -la", confidence=0.8)
        ]
        result = await consensus_manager.resolve("test goal", "context", proposals)
        
        print(f"DEBUG RESULT: {result}")
        print(f"Result logic: {result.get('synthesis_logic')}")
        print(f"Refined: {result.get('governance_refined')}")
        assert result.get("governance_refined") is True
        assert "safe" in result.get("hybrid_plan")
    print("[OK] Consensus refinement works.")

async def test_strategic_retrieval():
    print("\n--- [TEST] Goal Decomposer Strategic Retrieval ---")
    mock_cortex = AsyncMock()
    mock_cortex.search.return_value = [{"body": "Successful Plan A"}]
    
    with patch("packages.orchestration.agi.cognitive.goal_decomposer.synaptic_cortex", mock_cortex):
        with patch("packages.orchestration.agi.cognitive.goal_decomposer.get_db") as mock_db:
             goal_decomposer.model_orch = AsyncMock()
             goal_decomposer.model_orch.complete_task.return_value = MagicMock(content='{"plan": []}')
             
             await goal_decomposer.decompose("test title", "desc", [])
             
             # Check if LLM was called with the retrieved memory
             call_args = goal_decomposer.model_orch.complete_task.call_args
             prompt_sent = f"{call_args.kwargs['prompt']}"
             assert "Successful Plan A" in prompt_sent
    print("[OK] Strategic retrieval injected into prompt.")

async def test_resilience_recovery():
    print("\n--- [TEST] Sovereign Cortex Resilience Recovery ---")
    
    # Create a task with one subtask that will fail
    task = ProjectTask(id="test_proj", title="Test Recovery", subtasks=[
        SubTask(id="step_fail", agent_id="error_bot", prompt="fail me", status=TaskStatus.PENDING)
    ])
    
    # Mock execute_subtask_nexus to fail for the first subtask
    # We'll use a local mock for this instance of SovereignCortex
    mock_cortex_local = SovereignCortex()
    mock_orch = AsyncMock()
    mock_cortex_local.model_orch = mock_orch
    
    async def mock_execute(st, pt):
        if st.id == "step_fail":
            st.status = TaskStatus.ERROR
            st.result = "Critical failure"
        else:
            st.status = TaskStatus.COMPLETED
            st.result = "Repaired"
            
    mock_execute_shim = AsyncMock(side_effect=mock_execute)
    # Patch the instance method
    mock_cortex_local._execute_subtask_nexus = mock_execute_shim
    
    mock_decomposer = AsyncMock()
    mock_decomposer.decompose.return_value = [
        SubTask(id="step_repair", agent_id="fixer", prompt="fix it", status=TaskStatus.PENDING)
    ]
    
    # Mock other deps
    mock_cortex_local.synthesizer = MagicMock()
    mock_cortex_local._post_task_reflection = AsyncMock()
    mock_cortex_local.state_svc = MagicMock()
    mock_cortex_local.affective = MagicMock()
    mock_cortex_local.motivation = AsyncMock()
    mock_cortex_local.planner = AsyncMock()
    
    with patch("packages.orchestration.agi.cognitive.sovereign_cortex.goal_decomposer", mock_decomposer):
        with patch.object(mock_cortex_local, "_execute_dialectic_planning", AsyncMock(return_value=task)):
            with patch("packages.orchestration.agi.cognitive.sovereign_cortex.synaptic_cortex", AsyncMock()):
                with patch("packages.orchestration.agi.cognitive.sovereign_cortex.foresight_cortex", AsyncMock()):
                    with patch("packages.orchestration.agi.cognitive.sovereign_cortex.memory_api", AsyncMock()):
                        await mock_cortex_local.coordinate_goal("Test Recovery", "Desc")

    print(f"Final status: {task.status}")
    print(f"Total subtasks: {len(task.subtasks)}")
    # Should have 2 subtasks now (failed one + repaired one)
    assert len(task.subtasks) == 2
    assert task.status == TaskStatus.COMPLETED
    print("[OK] Resilience recovery successful.")

if __name__ == "__main__":
    asyncio.run(test_consensus_refinement())
    asyncio.run(test_strategic_retrieval())
    asyncio.run(test_resilience_recovery())
