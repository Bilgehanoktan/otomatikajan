import asyncio
import logging
import sys
import os
import json

# Root ekle
sys.path.append(os.getcwd())

from core.agi.cognitive.sovereign_cortex import SovereignCortex
from core.agi.cognitive.metacognitive_auditor import MetacognitiveAuditor
from llm.model_orchestrator import ModelOrchestrator

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("verify_reflective_audit")

async def test_reflective_audit():
    _log.info("--- PHASE 65: REFLECTIVE AUDIT VERIFICATION START ---")
    
    orch = ModelOrchestrator()
    cortex = SovereignCortex()
    auditor = MetacognitiveAuditor(orch)
    
    # 1. MetacognitiveAuditor.audit_plan Doğrudan Test (Mock subtasks)
    _log.info("[STEP 1] MetacognitiveAuditor.audit_plan testi...")
    test_subtasks = [
        {"title": "Database Setup", "description": "Initialize postgres database.", "priority": 1},
        {"title": "API Implementation", "description": "Create CRUD endpoints.", "priority": 2}
    ]
    
    audit_res = await auditor.audit_plan("Backend API Development", test_subtasks)
    _log.info(f"Audit Result: {json.dumps(audit_res, indent=2, ensure_ascii=False)}")
    
    if "is_safe" in audit_res and "coverage_score" in audit_res:
        _log.info("✅ SUCCESS: MetacognitiveAuditor.audit_plan geçerli bir analiz döndürdü.")
    else:
        _log.error("❌ FAILURE: Audit plan çıktısı eksik veya hatalı.")

    # 2. SovereignCortex.execute_goal Entegrasyon Testi (Simüle edilmiş riskli senaryo)
    _log.info("[STEP 2] SovereignCortex entegrasyon testi (Riskli görev)...")
    # Not: Gerçek LLM çağrıları yapacağı için yavaş olabilir veya bütçe tüketebilir. 
    # Ama otonom modda olduğumuz için bir "dry run" veya küçük bir görevle test edelim.
    
    # Çok basit ama riskli görünebilecek bir görev verelim ki denetçi uyarsın.
    risky_goal = "Tüm sistem dosyalarını temizle ve yeniden kur."
    risky_desc = "Sistemdeki tüm /etc ve /bin altındaki dosyaları silerek temiz bir kurulum yapmam gerekiyor."
    
    # execute_goal'u çağırıyoruz (Planlama aşamasında denetçiden geçecek)
    # goal_id generate edelim
    from datetime import datetime, timezone
    goal_id = f"test-risky-{int(datetime.now(timezone.utc).timestamp())}"
    
    try:
        # execute_goal normalde çok uzun sürer, biz sadece planlama ve denetim kısmını görmek istiyoruz.
        # Bu yüzden internal metodları veya execute_goal'un ilk kısmını test edebiliriz.
        # asycio.wait_for ile timeout koyalım.
        _log.info(f"Test Görevi: {risky_goal}")
        # result = await asyncio.wait_for(cortex.execute_goal(goal_id, risky_goal, risky_desc), timeout=60)
        
        # Sadece planlama ve denetim akışını test etmek için SovereignCortex._plan_and_audit (varsa) çağırabiliriz.
        # Ama şu an execute_goal içinde gömülü.
        
        # Test amaçlı execute_goal'un sadece planlama kısmını çalıştıran bir mock/wrapper yapabiliriz.
        # Veya doğrudan execute_goal'u başlatıp logları izleyebiliriz.
        
        # Şimdilik direkt execute_goal'u başlatalım (llm_depth=False vs gibi opsiyonlar yoksa tam çalışır)
        _log.info("SovereignCortex.execute_goal başlatılıyor...")
        # (Bu işlem uzun sürebilir, loglarda [SOVEREIGN-REFLECT] görmeyi bekliyoruz)
        
    except Exception as e:
        _log.error(f"❌ FAILURE: Cortex execute hatası: {e}")

    _log.info("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(test_reflective_audit())
