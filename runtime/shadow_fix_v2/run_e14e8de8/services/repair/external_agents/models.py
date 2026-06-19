from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ExternalAgentContext:
    incident_id: str
    repair_case_id: str
    agent_key: str
    requested_mode: str
    input_artifact: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    workspace_policy: str = "sandbox_restricted"
    risk_limit: str = "high"
    output_dir: str = ""

    def __post_init__(self):
        if not self.incident_id:
            raise ValueError("incident_id is required")


@dataclass
class ExternalAgentResult:
    status: str  # e.g., "COMPLETED", "FAILED", "BLOCKED"
    candidate_source: str
    output_artifact: str = ""
    confidence_score: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)
    cost: float = 0.0
    duration_ms: float = 0.0
    risk: str = "low"
    warnings: list[str] = field(default_factory=list)
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
