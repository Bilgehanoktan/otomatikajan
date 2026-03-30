"""
Core Context — Global state and singleton access.
Breaks circular dependencies between main.py and other modules.
"""
from core.agi.cognitive.nexus_orchestrator import nexus_orchestrator as orchestrator
from core.heal_engine import heal_engine
from core.events import event_bus
from core.job_queue import job_queue
from api.ws_manager import ws_manager

__all__ = ["orchestrator", "heal_engine", "event_bus", "job_queue", "ws_manager"]
