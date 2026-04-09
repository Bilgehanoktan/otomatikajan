"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'packages.orchestration.domain.models' ve 'packages.orchestration.application.governance' modüllerine yönlendirme yapmaktadır.
Yeni geliştirmelerde doğrudan 'application.governance' veya 'domain.models' kullanılmalıdır.
"""

from packages.orchestration.domain.models import (
    GovernanceStatus,
    GovernedTask,
    SovereignGoal
)

from packages.orchestration.application.governance import (
    TaskPlanner,
    TaskStateService,
    ReportSynthesizer
)

# Aliases for backward compatibility
ProjectTask = SovereignGoal
SubTask = GovernedTask
TaskStatus = GovernanceStatus
