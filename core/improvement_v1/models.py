from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class ImprovementOpportunity:
    id: str
    source_metric: str        # "agent_fail_rate", "endpoint_error_rate", etc.
    severity: str             # "low", "medium", "high", "critical"
    description: str
    affected_files: List[str]
    evidence: Dict[str, Any]  # Metric values, error samples
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PatchProposal:
    id: str
    opportunity_id: str
    target_file: str
    diff: str                 # standard unified diff format
    explanation: str          # LLM explanation
    risk_score: float         # 0.0 - 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class VerificationResult:
    proposal_id: str
    tests_passed: bool
    test_details: str
    benchmark_before: Dict[str, Any]
    benchmark_after: Dict[str, Any]
    security_ok: bool
    verified_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class GateDecision:
    proposal_id: str
    decision: str             # "approve", "reject", "abort"
    reason: str
    requires_human: bool = True
    decided_at: datetime = field(default_factory=datetime.utcnow)
