import asyncio
import logging
from packages.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex
from packages.orchestration.agi.packages.quality_assurance.agi_evaluator import agi_evaluator

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("phase_34_verif")

async def verify_phase_34():
    _log.info("Phase 34: Cognitive Mastery Verification starting...")
    
    # 1. Test Dynamic Planning
    cortex = SovereignCortex()
    title = "Test: Build a simple web server"
    description = "Create a FastAPI server with a single /health endpoint."
    
    _log.info("Testing Dynamic Planning via Dialectic Planning...")
    task = await cortex._execute_dialectic_planning("verif-34", title, "", description)
    
    _log.info(f"Dynamic Plan Steps: {[st.agent_id for st in task.subtasks]}")
    if len(task.subtasks) < 8: # Static plan was 9-11 packages.orchestration.agi. Dynamic should be fewer for this task.
        _log.info("SUCCESS: Dynamic Planning reduced task redundancy.")
    else:
        _log.warning("WARNING: Dynamic Planning still produced many packages.orchestration.agi. Check logic.")

    # 2. Test AGI Evaluator
    _log.info("Testing AGI Evaluator...")
    report = await agi_evaluator.run_suite()
    _log.info(f"AGI Index: {report['agi_index']}")
    
    _log.info("Phase 34 Verification COMPLETED.")

if __name__ == "__main__":
    asyncio.run(verify_phase_34())
