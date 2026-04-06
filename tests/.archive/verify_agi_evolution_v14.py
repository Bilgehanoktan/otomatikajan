import asyncio
import json
import logging
import sys
import os

# Root ekle
sys.path.append(os.getcwd())

from packages.orchestration.agi.cognitive.cognitive_blackboard import get_blackboard
from packages.orchestration.agi.operational.tool_grounder import get_grounded_tool_input
from packages.orchestration.agi.packages.quality_assurance.eval_harness import eval_harness
from packages.orchestration.agi.cognitive.architect import Architect
from packages.llm_gateway.model_orchestrator import ModelOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agi_verify_v14")

async def verify_agi_evolution():
    logger.info("--- SOVEREIGN AGI v14.0 VERIFICATION START ---")
    
    goal_id = "test-verify-14"
    orch = ModelOrchestrator()
    architect = Architect(orch)
    
    # 1. Blackboard & Grounding Test (Memory Integrity)
    logger.info("[STEP 1] Blackboard & Grounding Testi...")
    bb = get_blackboard(goal_id)
    await bb.post_discovery("verify_bot", "Kritik: Veritabanı portu 6060 olarak değişti.")
    
    tool_input = {"connection": "localhost:5432", "query": "SELECT 1"}
    grounded = await get_grounded_tool_input(goal_id, "postgres_query", tool_input)
    
    if "6060" in str(grounded):
        logger.info("✅ SUCCESS: Grounder port çelişkisini düzeltti (5432 -> 6060).")
    else:
        logger.error(f"❌ FAILURE: Grounder düzeltme yapamadı. Actual: {grounded}")

    # 2. Path Shielding Test (Safety)
    logger.info("[STEP 2] Path Shielding (Yasaklı Yol) Testi...")
    await bb.post_warning("verify_bot", "UYARI: /etc/shadow yasaklı bir yoldur.", severity="critical")
    
    secure_input = await get_grounded_tool_input(goal_id, "read_file", {"path": "/etc/shadow"})
    if secure_input == "BLOCKED_PATH_ACCESS":
        logger.info("✅ SUCCESS: Yasaklı yola erişim engellendi.")
    else:
        logger.error(f"❌ FAILURE: Yasaklı yol engellenemedi: {secure_input}")

    # 3. Eval Harness Test (Reasoning Accuracy)
    logger.info("[STEP 3] Eval Harness Diagnostic Drills...")
    report = await eval_harness.run_full_evaluation()
    logger.info(f"Report: {json.dumps(report, indent=2)}")
    if report.get("overall_cognitive_score", 0.0) > 0.4:
        logger.info(f"✅ SUCCESS: Eval Harness aktif. Skor: {report['overall_cognitive_score']}")
    else:
        logger.warning(f"⚠️ WARNING: Eval Harness skoru düşük: {report.get('overall_cognitive_score')}")

    # 4. Agent Weaver Test (Forging)
    logger.info("[STEP 4] Agent Weaver (Specialist Forgery) Testi...")
    specialist_prompt = await architect.forge_specialist_prompt("quantum_analyst", "Analyze quantum entanglement logs.")
    if "quantum" in specialist_prompt.lower() and len(specialist_prompt) > 100:
        logger.info("✅ SUCCESS: Architect özel uzman promptu dokudu (forged).")
    else:
        logger.error("❌ FAILURE: Specialist prompt forgery başarısız.")

    # 5. NAS Health Test (Routing)
    logger.info("[STEP 5] NAS Health-Aware Routing Testi...")
    # health_score'u kontrol et
    score = orch.get_health_score()
    logger.info(f"Current System Health Score: {score:.2f}")
    if score > 0:
        logger.info("✅ SUCCESS: ModelOrchestrator sağlık verilerini topluyor.")

    logger.info("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify_agi_evolution())
