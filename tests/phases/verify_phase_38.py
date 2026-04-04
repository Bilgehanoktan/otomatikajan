import asyncio
import logging
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from core.agi.cognitive.sovereign_cortex import SovereignCortex
from core.agi.task_governance import SovereignGoal, GovernedTask, TaskStatus, TaskPlanner
from core.agi.schemas import ActionRecord, VerificationReport, EpisodeRecord

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("phase_38_verif")

async def test_quality_gate_rollback():
    _log.info("Starting Phase 38 Verification: Autonomous Quality Gate & Rollback...")

    # 1. Initialize Cortex
    cortex = SovereignCortex()
    
    # 2. Create a simulated SovereignGoal (Task)
    task = SovereignGoal(
        id="t38",
        title="Quality Gate Test",
        status=TaskStatus.COMPLETED
    )

    # 3. Simulate a FAILED Episode Record (Baseline Score: 0.8)
    mock_action = ActionRecord(
        agent_id="backend_dev",
        tool_used="api_design",
        output_data="Bad API...",
        success=False
    )
    
    mock_episode = EpisodeRecord(
        episode_id="ep38",
        actions=[mock_action],
        lessons_learned=["Backend dev scope unclear."],
        metacognitive_score=0.8, # Baseline
        verification=VerificationReport(
            result_status=False,
            evidence_summary="API failed validation.",
            integration_reality_score=0.5
        )
    )

    # 4. Mock PromptSynthesizer to return a "Refined Contract"
    refined_contract = {
        "skill": "Backend Expert",
        "boundaries": "Strict boundaries",
        "expected_output": "Pydantic models"
    }
    cortex.prompt_synth.refine_contract = AsyncMock(return_value=refined_contract)

    # --- SCENARIO A: POISONED REFINEMENT (Score drops to 0.5) ---
    _log.info("Scenario A: Testing rejection of low-quality refinement...")
    
    with patch("core.agi.quality.agi_evaluator.agi_evaluator.run_suite", 
               return_value={"agi_index": 0.5, "scores": {}, "details": {}}), \
         patch("core.agi.learning.cognitive_mirror.cognitive_mirror.reflect", return_value=mock_episode), \
         patch("core.agi.learning.memory_gate.memory_gate.evaluate_eligibility", return_value=True), \
         patch("db.session.get_db"), \
         patch("core.agi.cognitive.synaptic_cortex.synaptic_cortex.save_episode"), \
         patch("core.agi.cognitive.synaptic_cortex.synaptic_cortex.save"):
        
        await cortex._post_task_reflection(task)
        
        # Verify rollback/rejection
        if "backend_dev" not in cortex.planner.dynamic_contracts:
            _log.info("✅ SUCCESS: Low-quality refinement rejected (as expected).")
        else:
            _log.error("❌ FAILURE: Low-quality refinement was applied!")
            return

    # --- SCENARIO B: IMPROVING REFINEMENT (Score stays high 0.9) ---
    _log.info("Scenario B: Testing acceptance of high-quality refinement...")
    
    with patch("core.agi.quality.agi_evaluator.agi_evaluator.run_suite", 
               return_value={"agi_index": 0.9, "scores": {}, "details": {}}), \
         patch("core.agi.learning.cognitive_mirror.cognitive_mirror.reflect", return_value=mock_episode), \
         patch("core.agi.learning.memory_gate.memory_gate.evaluate_eligibility", return_value=True), \
         patch("db.session.get_db"), \
         patch("core.agi.cognitive.synaptic_cortex.synaptic_cortex.save_episode"), \
         patch("core.agi.cognitive.synaptic_cortex.synaptic_cortex.save"):
        
        await cortex._post_task_reflection(task)
        
        # Verify acceptance
        if "backend_dev" in cortex.planner.dynamic_contracts:
            _log.info("✅ SUCCESS: High-quality refinement accepted.")
        else:
            _log.error("❌ FAILURE: High-quality refinement was rejected!")
            return

    _log.info("Phase 38 Verification COMPLETED.")

if __name__ == "__main__":
    asyncio.run(test_quality_gate_rollback())
