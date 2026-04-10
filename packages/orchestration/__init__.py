"""
Sovereign AGI Orchestration Package (Faz 12.1)
─────────────────────────────────────────────
Modular DDD structure for cognitive orchestration.
"""

# application katmanı (Services)
from packages.orchestration.application.orchestrator import central_executive as orchestrator
from packages.orchestration.application.control import system_control as control
from packages.orchestration.application.governance import TaskPlanner, TaskStateService, ReportSynthesizer

# domain katmanı (Business Models & Logic)
from packages.orchestration.domain.models import SovereignGoal, GovernedTask, GovernanceStatus, TaskStatus, ProjectTask, SubTask
from packages.orchestration.domain.auditor import metacognitive_auditor as auditor

__version__ = "12.1.0"
