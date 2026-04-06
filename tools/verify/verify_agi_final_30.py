"""
AGI Milestone 30.0 - Bilişsel ve Operasyonel Stabilizasyon Doğrulaması.
Faz 26-30 birimlerinin entegrasyonu test edilir.
"""
import asyncio
import sys
import os

# Path adjustment for local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.orchestration.agi.central_executive import CentralExecutive
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from packages.orchestration.agi.operational.resource_manager import resource_manager
from packages.orchestration.agi.operational.local_failsafe_engine import local_failsafe
from packages.persistence.session import session_scope, init_db
from packages.packages.observability.logging import get_logger

_log = get_logger("verify_agi_30")

async def verify_stitching():
    _log.info("--- TEST 1: Global Hafıza Bütünlüğü (Stitching) ---")
    async with session_scope() as db:
        # Önce birkaç yüksek önem dereceli memory ekleyelim (Simülasyon)
        await synaptic_cortex.save(db, "test_agent", "Kritik Güvenlik Kuralı: Şifreleri asla loglama.", category="policy_proposal", importance=0.95)
        await synaptic_cortex.save(db, "test_agent", "Performans Dersi: Büyük dosyaları chunk bazlı oku.", category="reflection_log", importance=0.85)
        await packages.persistence.commit()
        
        # Stitching tetikle
        await synaptic_cortex.synthesize_global_knowledge(db)
        
        # Evrensel dersleri kontrol et
        lessons = await synaptic_cortex.get_universal_lessons(db)
        _log.info(f"Sentezlenen Evrensel Ders Sayısı: {len(lessons)}")
        assert len(lessons) > 0, "Evrensel ders sentezlenemedi!"
    _log.info("Test 1 BAŞARILI.")

async def verify_resource_aware_failsafe():
    _log.info("--- TEST 2: Resource-Aware Fallback ---")
    exec_unit = CentralExecutive()
    
    # API hatası simüle et (429)
    resource_manager.report_error("openai", 429)
    guidance = resource_manager.get_strategy_guidance()
    _log.info(f"Resource Guidance Mode: {guidance['mode']}")
    
    # Central EXECUTIVE döngüsünü tetikle (Simüle edilmiş hata ile)
    failsafe_output = local_failsafe.generate_reflection("Kodumda bir hata var, düzelt.", "backend_dev")
    _log.info(f"Failsafe Cikti Ornegi:\n{failsafe_output}")
    assert "DEGRADED MODE" in failsafe_output or "OFFLINE REASONING" in failsafe_output
    _log.info("Test 2 BASARILI.")

async def main():
    _log.info("=== AGI MILESTONE 30.0 FINAL VERIFICATION ===")
    
    try:
        await init_db()
        await verify_stitching()
        await verify_resource_aware_failsafe()
        _log.info("=== TÜM TESTLER BAŞARIYLA TAMAMLANDI (SENTIENT CORE 30.0) ===")
    except Exception as e:
        import traceback
        _log.error(f"VERIFICATION FAILED with error [{type(e).__name__}]: {e}")
        _log.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
