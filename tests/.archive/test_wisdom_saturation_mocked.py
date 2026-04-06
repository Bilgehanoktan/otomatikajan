import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from packages.orchestration.agi.learning.wisdom_synthesizer import WisdomSynthesizer
from packages.orchestration.agi.task_governance import SovereignGoal, GovernedTask, GovernanceStatus
from packages.orchestration.agi.operational.metabolic_governor import MetabolicMode

async def test_saturation_mocked():
    print("--- Phase 60.6 Verification: Wisdom Saturation (MOCKED) ---")
    
    # 1. Setup Synthesizer with mocks
    synthesizer = WisdomSynthesizer()
    synthesizer.model_orch = MagicMock()
    # Mock return value of complete_task (ModelResponse-like)
    mock_resp = MagicMock()
    mock_resp.content = "New Wisdom"
    synthesizer.model_orch.complete_task = AsyncMock(return_value=mock_resp)
    
    # Mock DB interaction
    synthesizer._get_db = MagicMock()
    synthesizer._increment_importance = AsyncMock()
    synthesizer._parse_and_record_causality = AsyncMock()
    
    # 2. Create a dummy task
    task = SovereignGoal(
        id="test-task-sat",
        title="Optimization of CSS rendering",
        description="Reducing layout shifts."
    )
    # Add a completed subtask
    task.subtasks = [
        GovernedTask(id="st-1", agent_id="fe", prompt="fix css", status=GovernanceStatus.COMPLETED, result="fixed")
    ]
    
    # 3. Scenario A: No saturation (First call)
    print("\n[SCENARIO A] First Synthesis...")
    with patch("packages.orchestration.agi.learning.wisdom_synthesizer.synaptic_cortex.search", AsyncMock(return_value=[])):
        res1 = await synthesizer.synthesize_from_task(task)
        print(f"Result 1: {res1}")
        assert res1 == "New Wisdom"

    # 4. Scenario B: Saturation (Second call)
    print("\n[SCENARIO B] Second Synthesis (Same Task)...")
    # Mock a PERFECT matching memory for test
    mock_memory = {
        "id": "mem-1",
        "body": "Optimization of CSS rendering Reducing layout shifts.",
        "importance": 0.8
    }
    
    with patch("packages.orchestration.agi.learning.wisdom_synthesizer.synaptic_cortex.search", AsyncMock(return_value=[mock_memory])):
        with patch("packages.orchestration.agi.learning.wisdom_synthesizer.metabolic_governor.get_mode", return_value=MetabolicMode.NORMAL):
            # Similarity should be 1.0
            res2 = await synthesizer.synthesize_from_task(task)
            print(f"Result 2: {res2}")
            assert res2 == "SATURATED"
            # complete_task should NOT be called again (still 1 from Scenario A)
            assert synthesizer.model_orch.complete_task.call_count == 1 
            synthesizer._increment_importance.assert_awaited()

    print("\n✅ Phase 60.6 MOCKED Verification SUCCESS: Saturation logic correctly gates LLM calls.")

if __name__ == "__main__":
    asyncio.run(test_saturation_mocked())
