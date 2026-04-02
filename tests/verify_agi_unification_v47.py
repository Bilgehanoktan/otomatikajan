import asyncio
import logging
from core.agi.cognitive.sovereign_cortex import sovereign_cortex
from core.agi.cognitive.agi_goal_decomposer import agi_goal_decomposer
from core.agi.cognitive.metacognitive_auditor import metacognitive_auditor

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("VERIFY-V47")

async def test_unification():
    _log.info("--- Phase 47 Verification Started ---")
    
    # 1. Check imports and instances
    _log.info(f"Checking AgiGoalDecomposer: {agi_goal_decomposer}")
    assert agi_goal_decomposer is not None
    
    # 2. Test Decomposer Turkish Output (Simulation)
    _log.info("Simulating Task Decomposition (Turkish prompts)...")
    subtasks = await agi_goal_decomposer.decompose(
        title="Mimari Refaktör Testi",
        description="Sistemi otonom olarak daha modüler hale getir.",
        available_agents=[{"id": "architect", "role": "architect", "name": "Mimar"}]
    )
    
    _log.info(f"Generated {len(subtasks)} subtasks.")
    if len(subtasks) > 0:
        _log.info(f"Sample Prompt: {subtasks[0].prompt}")
    
    # 3. Test Metacognitive Auditor RCA (Turkish)
    _log.info("Testing Metacognitive Auditor RCA (Deep RCA)...")
    fail_analysis = await metacognitive_auditor.analyze_job_failure(
        job_type="research",
        job_payload={"path": "core/agi/cognitive/sovereign_cortex.py"},
        error_msg="Recursion depth exceeded",
        last_monologue="Trying to fix imports..."
    )
    
    _log.info(f"RCA Result: {fail_analysis.get('root_cause')}")
    assert "root_cause" in fail_analysis
    
    _log.info("--- Phase 47 Verification COMPLETED SUCCESSFULY ---")

if __name__ == "__main__":
    asyncio.run(test_unification())
