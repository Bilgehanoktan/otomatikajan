import asyncio
import logging
import os
import sys

# Ensure root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.agi.central_executive import central_executive
from core.agi.cognitive.thread_governor import thread_governor
from core.agi.operational.tool_grounder import get_grounded_tool_input
from core.agi.operational.velocity_engine import velocity_engine
from core.agi.schemas import SourceType

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("VERIFY_PHASE_63_65")

async def verify_phases():
    _log.info("--- PHASE 63-65 INTEGRITY VERIFICATION ---")
    
    # Mocking DB context
    mock_db = None 
    mock_project_id = "test_project_agi"
    
    # 1. Verify ThreadGovernor (Phase 63)
    _log.info("[TEST-63] Internal Monologue Verification...")
    try:
        # Note: This uses LLM call internally
        await thread_governor.update_thread(mock_db, mock_project_id, "Testing AGI continuity", "Success: Thread started")
        monologue = await thread_governor.get_active_thread(mock_db, mock_project_id)
        _log.info(f"Thread Monologue: {monologue}")
    except Exception as e:
        _log.error(f"ThreadGovernor failure: {e}")

    # 2. Verify ToolGrounder (Phase 64)
    _log.info("[TEST-64] Tool Grounding (World Model) Verification...")
    test_tool = "file_editor"
    test_input = {"path": "core/agi/cog_blackboard.py", "content": "print('hello')"} # Correct existing path
    
    try:
        grounded = await get_grounded_tool_input(mock_project_id, test_tool, test_input)
        _log.info(f"Grounded Input: {grounded}")
        
        # Test Halüsinasyon (Should suggest core/agi/cognitive/synaptic_cortex.py)
        hallucinated_input = {"path": "core/agi/synapse_cortex.py", "content": "print('hello')"}
        grounded_hallucinated = await get_grounded_tool_input(mock_project_id, test_tool, hallucinated_input)
        _log.info(f"Grounded Hallucinated Input: {grounded_hallucinated}")
    except Exception as e:
        _log.error(f"ToolGrounder failure: {e}")

    # 3. Verify VelocityEngine Simulation (Phase 65)
    _log.info("[TEST-65] Velocity Foresight Simulation Verification...")
    try:
        success, report = await velocity_engine._run_simulation("architect", "Create a new module for AGI security.", {"working_context": "Initial setup"})
        _log.info(f"Simulation Result: {success} | Report: {report}")
    except Exception as e:
        _log.error(f"VelocityEngine Simulation failure: {e}")

    _log.info("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify_phases())
