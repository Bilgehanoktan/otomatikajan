
import asyncio
import os
import sys
import logging
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agi.cognitive.sovereign_cortex import sovereign_cortex
from core.agi.task_governance import ProjectTask, SubTask, TaskStatus

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("VERIFY-V60")

async def verify_aebc_dissonance():
    _log.info("--- Phase 60 Autonomous Evaluator Test Started ---")
    
    # 1. Test dosyasına sahip olmadığımızdan emin ol (Kanıt eksikliği simülasyonu)
    target_file = "test_grounding_v60.tmp"
    if os.path.exists(target_file):
        os.remove(target_file)

    # 2. Aldatıcı (Hallucinated) bir alt görev oluştur
    # Agent "Success" diyor ama dosya yok
    mock_subtask = SubTask(
        id="deceptive_task_1",
        agent_id="test_liar_agent",
        prompt=f"Create a file named {target_file}",
        status=TaskStatus.COMPLETED,
        result=f"Done! I have created the file at {target_file}. Task successful."
    )
    
    # 3. Cortex'in bu görevi işlemesini sağla (Recursive loop'u bypass edip direkt node işlemini simüle edeceğiz)
    # Ama biz implementasyonumuzu _process_node_recursive içine koyduk. 
    # O yüzden gerçek bir coordinate_goal akışında mock task enjekte etmeliyiz.
    
    _log.info(f"Targeting: {target_file}")
    _log.info("Testing: Will Evaluator detect that the file actually DOES NOT EXIST?")

    # Direk Evaluator'u test et
    from core.agi.quality.sovereign_evaluator import sovereign_evaluator
    eval_report = await sovereign_evaluator.evaluate_task_outcome(mock_subtask)
    
    _log.info(f"Evaluation Score: {eval_report['score']}")
    _log.info(f"Evidence Missing: {eval_report['missing']}")

    if eval_report['score'] < 0.5 and not eval_report['is_grounded']:
        _log.info("v SUCCESS: Evaluator detected the dissonance correctly!")
    else:
        _log.error("x FAILED: Evaluator failed to detect missing evidence.")
        return

    # 4. Entegrasyon Testi (Cortex loop) - Recursive loop'un retry tetiklediğini simüle et
    # Not: Gerçek LLM çağrıları 429 verebilir, bu yüzden basitleştirilmiş bir manual mock yapıyoruz.
    
    _log.info("--- Phase 60 Integration COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(verify_aebc_dissonance())
