import asyncio
import sys
import os

# PYTHONPATH setting (For absolute imports)
sys.path.append(os.getcwd())

from packages.observability.logging import get_logger
from packages.orchestration.application.sovereign_cortex import SovereignCortex
from packages.healing.application.heal_engine import heal_engine
from packages.improvement_engine.self_improvement_coordinator import SelfImprovementCoordinator
from packages.orchestration.agi.cognitive.foresight_cortex import foresight_cortex
from packages.orchestration.agi.cognitive.reflective_synthesizer import reflective_synthesizer

_log = get_logger("integrity_checker")

async def verify_integrity():
    _log.info("[CHECK] Sovereign AGI Integrity Audit Starting...")
    errors = []

    # 1. SovereignCortex Connectivity
    try:
        cortex = SovereignCortex()
        _log.info("[OK] [CORTEX] Main orchestration engine reachable.")
    except Exception as e:
        errors.append(f"Cortex Initialization Failed: {e}")

    # 2. Self-Healing
    try:
        if heal_engine:
            _log.info("[OK] [HEALING] Autonomous heal engine connected.")
        else:
            errors.append("HealEngine instance is None.")
    except Exception as e:
        errors.append(f"HealEngine Check Failed: {e}")

    # 3. Self-Improvement
    try:
        from packages.improvement_engine.observer import observer
        if observer:
            _log.info("[OK] [IMPROVEMENT] Self-improvement observer active.")
        else:
            errors.append("Improvement Observer is None.")
    except Exception as e:
        errors.append(f"Improvement Check Failed: {e}")

    # 4. Foresight
    try:
        if foresight_cortex:
            _log.info("[OK] [FORESIGHT] Strategic foresight engine connected.")
        else:
            errors.append("ForesightCortex is None.")
    except Exception as e:
        errors.append(f"Foresight Check Failed: {e}")

    # 5. Reflection
    try:
        if reflective_synthesizer:
            _log.info("[OK] [REFLECTION] Cognitive reflection engine connected.")
        else:
            errors.append("ReflectiveSynthesizer is None.")
    except Exception as e:
        errors.append(f"Reflection Check Failed: {e}")

    # 6. Dashboard Integrity (UI/Logic Sync)
    try:
        from tools.maintenance.dashboard_guardian import check_dashboard_sync
        _log.info("[CHECK] [DASHBOARD] Interface layers audit starting...")
        if not check_dashboard_sync():
            errors.append("Dashboard Integrity Check Failed (Sync mismatch).")
        else:
            _log.info("[OK] [DASHBOARD] All layers (Sidebar/HTML/JS) synchronized.")
    except Exception as e:
        errors.append(f"Dashboard Guardian Check Failed: {e}")

    # RESULTS
    if not errors:
        _log.info("[SUCCESS] INTEGRITY VERIFIED: Sovereign AGI 100% ready for operations.")
        return True
    else:
        _log.error("[ERROR] INTEGRITY FAILURE: The following modules are missing or broken:")
        for err in errors:
            _log.error(f"  - {err}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_integrity())
    if not success:
        sys.exit(1)
    sys.exit(0)
