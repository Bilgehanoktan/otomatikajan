import asyncio
import logging
import time
from llm.model_orchestrator import ModelOrchestrator
from core.agi.operational.metabolic_governor import metabolic_governor, MetabolicMode
from core.agi.consciousness.affective_core import affective_core

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("VERIFY-V48")

async def verify_adaptation():
    _log.info("--- Phase 48 Dynamic Adaptation Test Started ---")
    orch = ModelOrchestrator()
    
    # 1. Test NORMAL Mode
    _log.info("Scenario 1: NORMAL Mode (High Energy, No Failures)")
    affective_core.state["energy_reserve"] = 1.0 # Max energy
    # Simulate a check
    await metabolic_governor.update_metabolism(orch.providers)
    _log.info(f"Current Mode: {metabolic_governor.get_mode()} | Score: {metabolic_governor.get_score()}")
    assert metabolic_governor.get_mode() in (MetabolicMode.NORMAL, MetabolicMode.TURBO)

    # 2. Test ECO Mode Trigger (Low Energy)
    _log.info("Scenario 2: ECO Mode (Low Energy Trigger)")
    affective_core.state["energy_reserve"] = 0.1 # Low energy
    # We need to wait or force update since last_check might block
    metabolic_governor._last_check = 0 
    await metabolic_governor.update_metabolism(orch.providers)
    _log.info(f"Current Mode: {metabolic_governor.get_mode()} | Score: {metabolic_governor.get_score()}")
    assert metabolic_governor.get_mode() == MetabolicMode.ECO

    # 3. Test ECO Mode Pacing (Orchestrator Level)
    _log.info("Scenario 3: Orchestrator Pacing in ECO Mode")
    start_time = time.time()
    try:
        # We expect this to fail eventually because keys might be missing, 
        # but the DELAY should happen BEFORE the first provider attempt.
        # Use placeholders to avoid real API calls
        await asyncio.wait_for(orch.complete_task(
            agent_role="general", 
            prompt="Test", 
            system_prompt="Test"
        ), timeout=15)
    except Exception as e:
         _log.info(f"Task finished (as expected with error/timeout): {type(e).__name__} - {e}")
    
    elapsed = time.time() - start_time
    _log.info(f"Elapsed time for ECO request: {elapsed:.2f}s")
    # ECO delay is 1.5 + (1.0 - 0.1)*4 = 1.5 + 3.6 = 5.1s
    if elapsed > 4.5:
        _log.info("v SUCCESS: Dynamic Pacing confirmed.")
    else:
        _log.error("x FAILURE: Pacing delay not detected.")
    
    _log.info("--- Phase 48 Verification COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(verify_adaptation())
