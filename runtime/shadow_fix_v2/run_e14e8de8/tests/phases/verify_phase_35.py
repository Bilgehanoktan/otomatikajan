import asyncio
import logging
from services.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex
from services.orchestration.agi.consciousness.affective_core import affective_core
from services.orchestration.agi.learning.knowledge_distiller import knowledge_distiller
from services.orchestration.agi.quality.sovereign_evaluator import agi_evaluator

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("phase_35_verif")

async def verify_phase_35():
    _log.info("Phase 35: Metacognitive Resonance Verification starting...")
    
    # 1. Test Affective Coupling (Stresli Durumda Planlama)
    cortex = SovereignCortex()
    
    _log.info("[TEST-A] Yüksek STRES durumunda planlama testi...")
    affective_core.adjust_state("error", magnitude=0.5) # Stress fırlar
    
    title = "Kritik Güvenlik Yaması"
    description = "Sistemdeki yetkisiz erişim açıklarını kontrol et ve kapat."
    
    # Affective state'i elle inject edelim (Cortex normalde içinden okur ama doğrulamak için)
    aff_state = affective_core.get_state_matrix()
    task_stressed = await cortex._execute_dialectic_planning("verif-35-stress", title, "", description, aff_state)
    
    _log.info(f"Stresli Plan Adımları: {[st.agent_id for st in task_stressed.subtasks]}")
    # Beklenti: security ve qa_engineer gibi ajanların seçilmesi
    
    # 2. Test Collaborative Consult
    _log.info("[TEST-B] Collaborative Reasoning (Consultation) simülasyonu...")
    from services.orchestration.agi.cognitive.collaborative_node import collaborative_node
    ans = await collaborative_node.consult(
        requesting_agent="backend_dev",
        target_specialist="security",
        current_work="FastAPI ile veri tabanı bağlantısı kuruyorum.",
        question="SQL Injection riskinden kaçınmak için pydantic yeterli mi?"
    )
    _log.info(f"Danışma Yanıtı: {ans[:200]}...")

    # 3. Test Knowledge Distillation
    _log.info("[TEST-C] Knowledge Distillation testi...")
    test_episodes = [
        {"episode_id": "ep1", "final_output": "Security leak closed by using parameterized queries."},
        {"episode_id": "ep2", "final_output": "Fixed SQL injection vulnerability in user login module."}
    ]
    instincts = await knowledge_distiller.distill_instincts(test_episodes)
    _log.info(f"Damıtılan İçgüdü Sayısı: {len(instincts)}")

    # 4. Final AGI Score
    _log.info("Final AGI Score Evaluation...")
    report = await agi_evaluator.run_suite()
    _log.info(f"AGI Index: {report['agi_index']}")

    _log.info("Phase 35 Verification COMPLETED.")

if __name__ == "__main__":
    asyncio.run(verify_phase_35())
