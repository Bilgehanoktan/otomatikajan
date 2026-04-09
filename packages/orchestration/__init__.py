"""
Sovereign AGI Orchestration Package (Faz 12.1)
─────────────────────────────────────────────
Modular DDD structure for cognitive orchestration.
"""

# application katmanı (Services)
from .application.orchestrator import central_executive as orchestrator
from .application.control import system_control as control
from .application.governance import TaskPlanner, TaskStateService, ReportSynthesizer

# domain katmanı (Business Models & Logic)
from .domain.models import *
from .domain.auditor import metacognitive_auditor as auditor

__version__ = "12.1.0"
