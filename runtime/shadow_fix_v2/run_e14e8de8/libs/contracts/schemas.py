"""
Compatibility shim: schemas → libs.contracts.*
[MIGRATION] Tüm yeni kodlar doğrudan libs.contracts altındaki modülleri kullanmalıdır.
"""
from libs.contracts.states import TaskState, DeerFlowEventType, AgentStatus, ArtifactType
from libs.contracts.artifacts import Artifact
from libs.contracts.errors import ErrorDetail
from libs.contracts.agents import AgentContribution, SubtaskOutput
from libs.contracts.reports import FinalReport

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
