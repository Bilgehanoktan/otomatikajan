"""
Core Context — Global state and singleton access.
Breaks circular dependencies between main.py and other modules.
"""
# Centralized Core Artifacts (Faz 12.1 Refactored)
from services.orchestration.domain.events import event_bus
from services.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
from services.repair.application.heal_engine import heal_engine
# job_queue ve diğerleri için de paket yollarını kullanın
try:
    from services.orchestration.application.job_queue import job_queue
except ImportError:
    job_queue = None

__all__ = ["orchestrator", "heal_engine", "event_bus", "job_queue"]
