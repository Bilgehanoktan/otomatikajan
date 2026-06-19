"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'services.orchestration.domain.models' ve 'services.orchestration.application.governance' modüllerine yönlendirme yapmaktadır.
Yeni geliştirmelerde doğrudan 'application.governance' veya 'hub_cortex.domain.models' kullanılmalıdır.
"""

from services.orchestration.domain.models import (
    GovernanceStatus,
    GovernedTask,
    SovereignGoal
)

from services.orchestration.application.governance import (
    TaskPlanner,
    TaskStateService,
    ReportSynthesizer
)

# Aliases for backward compatibility
ProjectTask = SovereignGoal
SubTask = GovernedTask
TaskStatus = GovernanceStatus
