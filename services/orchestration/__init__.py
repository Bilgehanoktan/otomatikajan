"""
Sovereign AGI Orchestration Package (Faz 12.1)
─────────────────────────────────────────────
Modular DDD structure for cognitive services.orchestration.
"""

# Faz 12.1: Circular Import Prevention
# Bu dosyada üst seviye importlar (özellikle application katmanı) sirküler bağımlılığa yol açmaktadır.
# Gerektiğinde 'services.orchestration.application.orchestrator' vb. şeklinde spesifik import yapılmalıdır.

# from services.orchestration.application.orchestrator import central_executive as orchestrator
# from services.orchestration.application.control import system_control as control
# from services.orchestration.application.governance import TaskPlanner, TaskStateService, ReportSynthesizer

# from services.orchestration.domain.models import SovereignGoal, GovernedTask, GovernanceStatus, TaskStatus, ProjectTask, SubTask
# from services.orchestration.domain.auditor import metacognitive_auditor as auditor

__version__ = "12.1.0"
