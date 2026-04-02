"""
Compatibility shim: core.schemas → schemas (root)
[CONSOLIDATION] Bu dosya artık root schemas.py'nin bir re-export'udur.
Tüm yeni import'lar doğrudan `from schemas import ...` kullanmalıdır.
"""
from schemas import (
    TaskState,
    DeerFlowEventType,
    AgentStatus,
    ArtifactType,
    Artifact,
    ErrorDetail,
    SubtaskOutput,
    AgentContribution,
    FinalReport,
)

__all__ = [
    "TaskState",
    "DeerFlowEventType",
    "AgentStatus",
    "ArtifactType",
    "Artifact",
    "ErrorDetail",
    "SubtaskOutput",
    "AgentContribution",
    "FinalReport",
]
