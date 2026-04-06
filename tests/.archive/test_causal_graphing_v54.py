
import asyncio
import os
import sys
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.orchestration.agi.task_governance import ProjectTask, SubTask, TaskStatus
from packages.orchestration.agi.learning.wisdom_synthesizer import wisdom_synthesizer
from packages.orchestration.agi.world.causal_error_graph import causal_error_graph

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("VERIFY-V54")

async def verify_causal_graphing():
    _log.info("--- Phase 54 Causal Graphing Test Started ---")
    
    # 1. Başarısız bir görev simüle et
    task = ProjectTask(id="causal-test-task", title="Test Causal Extraction")
    task.description = "API endpoint entegrasyonu testi."
    task.status = TaskStatus.ERROR
    
    st = SubTask(id="st-fail", agent_id="backend_dev", prompt="Fix API Endpoint")
    st.status = TaskStatus.ERROR
    st.result = "Error: Connection refused at port 8080. Root cause: The docker container was not started."
    st.internal_monologue = "Docker konteynerı ayaklanmadan API test etmeye çalıştım, hata bu."
    
    task.subtasks = [st]
    
    _log.info("Scenario: Extracting Causality from Failure Trace")
    
    # 2. Sentezi çalıştır
    content = await wisdom_synthesizer.synthesize_from_task(task)
    
    if content:
        _log.info(f"v LLM Response Received: {content[:100]}...")
        
        # 3. CausalErrorGraph'ı kontrol et
        patterns = causal_error_graph.get_patterns_for_agent("backend_dev")
        
        found = False
        for p in patterns:
            if "docker" in p.root_cause.lower() or "docker" in p.preventive_action.lower():
                _log.info(f"v SUCCESS: Causal pattern found in WorldModel!")
                _log.info(f"  > Pattern ID: {p.pattern_id}")
                _log.info(f"  > Root Cause: {p.root_cause}")
                _log.info(f"  > Action: {p.preventive_action}")
                found = True
                break
        
        if not found:
            _log.error("x FAILED: Causal pattern not recorded in CausalErrorGraph. Check LLM output format.")
    else:
        _log.error("x FAILED: Wisdom synthesis returned None.")

    _log.info("--- Phase 54 Verification COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(verify_causal_graphing())
