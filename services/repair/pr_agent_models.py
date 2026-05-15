from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class PRAgentReviewRequest:
    pr_url: str
    case_id: str
    action: str # describe | review | improve | full-review

@dataclass
class PRAgentFinding:
    file_path: str
    line_number: int
    severity: str
    category: str
    message: str
    suggestion: Optional[str] = None

@dataclass
class PRAgentReviewResult:
    review_id: str
    pr_url: str
    status: str # PASSED | CHANGES_REQUESTED | FAILED
    summary: str
    governance_decision: str = "PENDING" # PASSED | BLOCKED | PENDING
    findings: List[PRAgentFinding] = field(default_factory=list)
    raw_output: Optional[str] = None
