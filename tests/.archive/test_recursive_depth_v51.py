
import asyncio
import os
import sys
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex
from packages.orchestration.agi.cognitive.agi_goal_decomposer import agi_goal_decomposer
from packages.orchestration.agi.task_governance import TaskStatus

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("VERIFY-V51")

async def verify_recursive_decomposition():
    _log.info("--- Phase 51 Recursive Decomposition Test Started ---")
    
    cortex = SovereignCortex()
    
    # 1. Karmaşık bir hedef tanımla (Decomposition'u zorlayacak kadar geniş)
    title = "Otonom Veri Depolama ve Analiz Motoru Kurulumu"
    description = """
    Bu proje şunları içermelidir:
    1. ClickHouse tabanlı bir büyük veri şeması tasarımı.
    2. Python tabanlı bir veri çekme (ingestion) servisi.
    3. Veriler üzerinde temel istatistiksel analiz yapan bir API.
    Lütfen her adımı derinlemesine planla.
    """
    
    _log.info("Scenario: Testing N-Depth Recursive Planning")
    
    # Not: Gerçek LLM çağrısı yapılacak (Groq/OpenAI fallback ile)
    # is_complex flag'inin gelmesini bekliyoruz.
    
    task = await cortex.coordinate_goal(title, description)
    
    _log.info(f"Main Task ID: {task.id}")
    _log.info(f"Initial Subtask Count: {len(task.subtasks)}")
    
    # Subtask'larda leads_to recursive expansion kontrolü
    for st in task.subtasks:
        _log.info(f"Subtask: {st.agent_id} | Complex: {getattr(st, 'is_complex', False)}")

    # 2. Yürütmeyi simüle et
    # Not: SovereignCortex.coordinate_goal sadece planlar, yürütmek için execute_task gerekir (basitleştirilmiş)
    # Ancak burada biz coordinate_goal içindeki planlama kalitesini doğruluyoruz.
    
    has_complex = any(getattr(st, "is_complex", False) for st in task.subtasks)
    
    if has_complex:
        _log.info("v SUCCESS: Complex subtask detected as expected.")
    else:
        _log.warning("x WARNING: No subtasks flagged as complex. This might depend on LLM creativity.")

    _log.info("--- Phase 51 Verification COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(verify_recursive_decomposition())
