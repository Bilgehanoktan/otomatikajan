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
    _log.info("[INTEGRITY] Sovereign AGI Bilisel Bütünlük Denetimi Baslatiliyor...")
    errors = []

    # 1. SovereignCortex Bağlantısı
    try:
        cortex = SovereignCortex()
        _log.info("[OK] [CORTEX] Ana orkestrasyon motoru erisilebilir.")
    except Exception as e:
        errors.append(f"Cortex Initialization Failed: {e}")

    # 2. Self-Healing (Bilişsel Onarım)
    try:
        from packages.healing.application.heal_engine import heal_engine
        if heal_engine:
            _log.info("[OK] [HEALING] Otonom onarim motoru bagli.")
        else:
            errors.append("HealEngine instance is None.")
    except Exception as e:
        errors.append(f"HealEngine Check Failed: {e}")


    # 3. Self-Improvement (Öz-Evrim)
    try:
        # Coordinator testi
        from packages.improvement_engine.observer import observer
        if observer:
            _log.info("[OK] [IMPROVEMENT] Oz-evrim gozlemcisi aktif.")
        else:
            errors.append("Improvement Observer is None.")
    except Exception as e:
        errors.append(f"Improvement Check Failed: {e}")

    # 4. Foresight (Öngörü)
    try:
        if foresight_cortex:
            _log.info("[OK] [FORESIGHT] Stratejik ongorü motoru bagli.")
        else:
            errors.append("ForesightCortex is None.")
    except Exception as e:
        errors.append(f"Foresight Check Failed: {e}")

    # 5. Reflection (Yansıtma)
    try:
        if reflective_synthesizer:
            _log.info("[OK] [REFLECTION] Bilisel denetim (Reflection) motoru bagli.")
        else:
            errors.append("ReflectiveSynthesizer is None.")
    except Exception as e:
        errors.append(f"Reflection Check Failed: {e}")

    # 6. Dashboard Bütünlüğü (UI/Logic Sync)
    try:
        from tools.maintenance.dashboard_guardian import check_dashboard_sync
        _log.info("[SEARCH] [DASHBOARD] Arayüz katmanları denetleniyor...")
        if not check_dashboard_sync():
            errors.append("Dashboard Integrity Check Failed (Sync mismatch).")
        else:
            _log.info("[OK] [DASHBOARD] Tum katmanlar (Sidebar/HTML/JS) senkronize.")
    except Exception as e:
        errors.append(f"Dashboard Guardian Check Failed: {e}")

    # SONUÇ
    if not errors:
        _log.info("[SUCCESS] BÜTÜNLÜK DOGRULANDI: Sovereign AGI operasyon icin %100 hazır.")
        return True
    else:
        _log.error("[ERROR] BÜTÜNLÜK HATASI: Asagidaki motorlar eksik veya hatali:")
        for err in errors:
            _log.error(f"  - {err}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_integrity())
    if not success:
        sys.exit(1)
    sys.exit(0)
