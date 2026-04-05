
import asyncio
import os
import sys
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agi.cognitive.sovereign_cortex import SovereignCortex
from core.agi.task_governance import ProjectTask, SubTask, TaskStatus
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("VERIFY-V53")

async def verify_wisdom_loop():
    _log.info("--- Phase 53 Wisdom Loop Test Started ---")
    
    cortex = SovereignCortex()
    
    # 1. Başarılı bir görev simüle et
    task = ProjectTask(id="test-wisdom-task", title="Test Wisdom Extraction")
    task.description = "Bu görev ClickHouse ve Zookeeper entegrasyonu ile ilgilidir."
    task.status = TaskStatus.COMPLETED
    task.report = "Zookeeper bağlantısı sağlandıktan sonra ClickHouse başarıyla kuruldu."
    
    st = SubTask(id="st-1", agent_id="backend_dev", prompt="Install ClickHouse")
    st.status = TaskStatus.COMPLETED
    st.result = "ClickHouse installation success. Note: Had to wait for zookeeper-seed node."
    st.internal_monologue = "Zookeeper ready'ye bakmadan başlarsak ClickHouse çöküyor. Bunu öğrendim."
    
    task.subtasks = [st]
    
    _log.info("Scenario: Synthesizing Wisdom from Simulated Success")
    
    # 2. Wisdom Synthesizer'ı direkt çağır (Cortex'in async trigger'ını simüle etmek yerine sonucunu ölçmek için)
    from core.agi.learning.wisdom_synthesizer import wisdom_synthesizer
    
    wisdom = await wisdom_synthesizer.synthesize_from_task(task)
    
    if wisdom:
        _log.info(f"v SUCCESS: Wisdom synthesized: {wisdom}")
        
        # 3. DB'de olup olmadığını doğrula
        async with AsyncSessionLocal() as db:
            memories = await synaptic_cortex.search(db, "ClickHouse Zookeeper", category="semantic_wisdom", top_k=1)
            if memories:
                _log.info(f"v SUCCESS: Wisdom found in SynapticCortex: {memories[0].body[:50]}...")
            else:
                _log.error("x FAILED: Wisdom not found in DB.")
    else:
        _log.error("x FAILED: Wisdom synthesis returned None.")

    _log.info("--- Phase 53 Verification COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(verify_wisdom_loop())
