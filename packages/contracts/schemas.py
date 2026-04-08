"""
Compatibility shim: schemas → packages.contracts.*
[MIGRATION] Tüm yeni kodlar doğrudan packages.contracts altındaki modülleri kullanmalıdır.
"""
from packages.contracts.states import TaskState, DeerFlowEventType, AgentStatus, ArtifactType
from packages.contracts.artifacts import Artifact
from packages.contracts.errors import ErrorDetail
from packages.contracts.agents import AgentContribution, SubtaskOutput
from packages.contracts.reports import FinalReport

__all__ = [
    "TaskState",
    "DeerFlowEventType",
    "AgentStatus",
    "ArtifactType",
    "Artifact",
    "ErrorDetail",
    "AgentContribution",
    "SubtaskOutput",
    "FinalReport",
]
