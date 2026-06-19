from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SuggestionStatus(str, Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    APPROVED_FOR_REPAIR = "APPROVED_FOR_REPAIR"
    APPROVED_FOR_PROJECT_FACTORY = "APPROVED_FOR_PROJECT_FACTORY"
    WAR_ROOM_RECOMMENDED = "WAR_ROOM_RECOMMENDED"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"
    MORE_EVIDENCE_REQUESTED = "MORE_EVIDENCE_REQUESTED"

@dataclass
class Finding:
    finding_id: str
    title: str
    description: str
    category: str
    severity: str  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    priority_score: int
    source: str
    affected_files: List[str] = field(default_factory=list)
    affected_endpoints: List[str] = field(default_factory=list)
    recommended_action: str = ""
    suggested_workflow: str = "self_repair_v1"
    requires_human_approval: bool = True
    evidence_refs: List[str] = field(default_factory=list)
    status: str = "NEW"

    def to_dict(self):
        return asdict(self)

@dataclass
class AuditRunArtifact:
    audit_run_id: str
    scanner: str
    status: str  # PASSED | WARNING | FAILED
    findings: List[Finding] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        d = asdict(self)
        # Serialize findings properly
        d["findings"] = [f.to_dict() if isinstance(f, Finding) else f for f in self.findings]
        return d
