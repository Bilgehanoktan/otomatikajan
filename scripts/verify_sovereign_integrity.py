import asyncio
import sys
import os

# PYTHONPATH ayarı (Absolute imports için)
sys.path.append(os.getcwd())

from packages.observability.logging import get_logger
from packages.orchestration.application.sovereign_cortex import SovereignCortex
from packages.healing.application.heal_engine import heal_engine
from packages.improvement_engine.self_improvement_coordinator import SelfImprovementCoordinator
from packages.orchestration.agi.cognitive.foresight_cortex import foresight_cortex
from packages.orchestration.agi.cognitive.reflective_synthesizer import reflective_synthesizer

_log = get_logger("integrity_checker")

async def verify_integrity():
    _log.info("🛡️ Sovereign AGI Bilişsel Bütünlük Denetimi Başlatılıyor...")
    errors = []

    # 1. SovereignCortex Bağlantısı
    try:
        cortex = SovereignCortex()
        _log.info("✅ [CORTEX] Ana orkestrasyon motoru erişilebilir.")
    except Exception as e:
        errors.append(f"Cortex Initialization Failed: {e}")

    # 2. Self-Healing (Bilişsel Onarım)
    try:
        from packages.healing.application.heal_engine import HealEngine
        if heal_engine:
            _log.info("✅ [HEALING] Otonom onarım motoru bağlı.")
        else:
            errors.append("HealEngine instance is None.")
    except Exception as e:
        errors.append(f"HealEngine Check Failed: {e}")

    # 3. Self-Improvement (Öz-Evrim)
    try:
        # Coordinator testi
        from packages.improvement_engine.observer import observer
        if observer:
            _log.info("✅ [IMPROVEMENT] Öz-evrim gözlemcisi aktif.")
        else:
            errors.append("Improvement Observer is None.")
    except Exception as e:
        errors.append(f"Improvement Check Failed: {e}")

    # 4. Foresight (Öngörü)
    try:
        if foresight_cortex:
            _log.info("✅ [FORESIGHT] Stratejik öngörü motoru bağlı.")
        else:
            errors.append("ForesightCortex is None.")
    except Exception as e:
        errors.append(f"Foresight Check Failed: {e}")

    # 5. Reflection (Yansıtma)
    try:
        if reflective_synthesizer:
            _log.info("✅ [REFLECTION] Bilişsel denetim (Reflection) motoru bağlı.")
        else:
            errors.append("ReflectiveSynthesizer is None.")
    except Exception as e:
        errors.append(f"Reflection Check Failed: {e}")

    # SONUÇ
    if not errors:
        _log.info("🔥 BÜTÜNLÜK DOĞRULANDI: Sovereign AGI operasyon için %100 hazır.")
        return True
    else:
        _log.error("❌ BÜTÜNLÜK HATASI: Aşağıdaki motorlar eksik veya hatalı:")
        for err in errors:
            _log.error(f"  - {err}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_integrity())
    if not success:
        sys.exit(1)
    sys.exit(0)
