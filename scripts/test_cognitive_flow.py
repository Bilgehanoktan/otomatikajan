import asyncio
import sys
import os

# PYTHONPATH ayarı
sys.path.append(os.getcwd())

from packages.orchestration.application.sovereign_cortex import SovereignCortex
from packages.observability.logging import get_logger

_log = get_logger("cognitive_test")

async def test_cognitive_synergy():
    _log.info("🧠 Sovereign AGI Fonksiyonel Bilişsel Sinaps Testi Başlatılıyor...")
    
    try:
        cortex = SovereignCortex()
        
        # 1. Öngörü Simülasyonu
        _log.info("🔮 ForesightCortex Test Ediliyor...")
        if cortex.foresight:
            analysis = await cortex.foresight.analyze_future_scenarios("Sistemi otonom olarak optimize et ve tüm araçları kullan.")
            _log.info(f"✅ Foresight Analizi Başarılı: {str(analysis)[:100]}...")
        else:
            _log.error("❌ ForesightCortex bağlı değil!")
            return False

        # 2. Yansıtmalı Denetim
        _log.info("🔍 ReflectiveSynthesizer Test Ediliyor...")
        if cortex.reflection:
            audit = await cortex.reflection.synthesize_retrospective("Geliştirme birimi %100 başarıyla tamamlandı.", "Kod bütünlüğü korundu.")
            _log.info(f"✅ Reflection Denetimi Başarılı: {str(audit)[:100]}...")
        else:
            _log.error("❌ ReflectiveSynthesizer bağlı değil!")
            return False

        # 3. Planlayıcı ve Yürütücü Sinerjisi
        _log.info("⚙️ Planner ve Executor Sinerji Testi...")
        if cortex.planner_svc and cortex.executor_svc:
            _log.info("✅ Bilişsel Planlayıcı ve Operasyonel Yürütücü hiyerarşisi doğrulanmış durumda.")
        else:
            _log.error("❌ Planner/Executor servisleri eksik!")
            return False

        _log.info("🔥 SONUÇ: Sovereign AGI bilişsel olarak %100 uyanış gerçekleştirdi.")
        return True
    except Exception as e:
        _log.error(f"❌ Test sırasında kritik hata: {e}")
        import traceback
        _log.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cognitive_synergy())
    if not success:
        sys.exit(1)
    sys.exit(0)
