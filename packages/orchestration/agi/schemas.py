"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'packages.orchestration.domain.models' modülüne yönlendirme yapmaktadır.
Yeni projelerde doğrudan 'domain.models' kullanılmalıdır.
"""

from packages.orchestration.domain.models import (
    SourceType,
    UnifiedInput,
    RiskLevel,
    TaskType,
    ProblemFrame,
    ContextPackage,
    PlanStep,
    PlanProposal,
    ExecutionPlan,
    ActionRecord,
    VerificationReport,
    AffectiveState,
    CausalLink,
    CausalGraph,
    EpisodeRecord,
    SkillArtifact,
    PolicyProposal
)
