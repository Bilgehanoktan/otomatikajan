from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


FINAL_STATUSES = {
    "REPAIR_CASE_CREATED",
    "LOCALIZATION_COMPLETED",
    "PATCH_PROPOSED",
    "SANDBOX_PASSED",
    "SANDBOX_FAILED",
    "VERIFIER_PASSED",
    "VERIFIER_FAILED",
    "HUMAN_APPROVAL_REQUIRED",
    "QUORUM_REQUIRED",
    "AUTO_REPAIR_BLOCKED",
    "DRAFT_PR_READY",
    "REPAIR_FAILED",
}


DEFAULT_FORBIDDEN_PATHS = [
    ".env",
    "secrets/",
    "migrations/production/",
    "services/auth/",
    "libs/config.py",
    "constitutional_guard.py",
    "governance critical files",
    "docker-compose.prod.yml",
    "infra/production/",
    "deploy/production/",
]


HIGH_RISK_PATH_MARKERS = [
    "services/auth/",
    "governance",
    "constitutional_guard.py",
    "libs/config.py",
    ".env",
    "secret",
    "migrations/",
    "rollback",
    "budget",
    "cost",
    "docker-compose.prod.yml",
    "deploy",
]


@dataclass
class RepairCase:
    incident_id: str
    trace_id: str = ""
    error_type: str = ""
    summary: str = ""
    failed_command: str = ""
    failed_test: str = ""
    traceback: str = ""
    related_logs: list[str] = field(default_factory=list)
    repo_snapshot: dict[str, Any] = field(default_factory=dict)
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=lambda: list(DEFAULT_FORBIDDEN_PATHS))
    suspected_files: list[str] = field(default_factory=list)
    context_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RepairCandidate:
    candidate_id: str
    patch_path: str
    changed_files: list[str] = field(default_factory=list)
    agent_summary: str = ""
    commands_run: list[str] = field(default_factory=list)
    confidence: float = 0.0
    status: str = "PATCH_PROPOSED"


@dataclass
class RepairPlan:
    repair_plan_id: str
    incident_id: str
    root_cause_hypothesis: str = ""
    target_files: list[str] = field(default_factory=list)
    expected_fix_type: str = "code_change"
    expected_tests: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    rollback_strategy: str = "Revert candidate patch from sandbox branch or discard draft PR."
    confidence: float = 0.0


@dataclass
class SandboxResult:
    patch_applied: bool = False
    tests_passed: bool = False
    failed_commands: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    exit_code: int = 0


@dataclass
class RepairDecision:
    status: str
    risk_score: float
    risk_level: str
    recommended_action: str
    reason: str


@dataclass
class RepairReport:
    repair_case: RepairCase
    suspected_files: list[dict[str, Any]]
    candidate: RepairCandidate
    sandbox_result: SandboxResult
    verifier_result: dict[str, Any]
    risk_decision: RepairDecision
    final_status: str
    repair_plan: RepairPlan | None = None


@dataclass
class UIRepairPRReview:
    review_id: str
    case_id: str
    pr_url: str
    status: str  # PENDING | RUNNING | PASSED | CHANGES_REQUESTED | BLOCKED | FAILED | MANUAL_REVIEW_REQUIRED
    summary: str = ""
    confidence_score: float = 0.0
    verifier_mesh_pass: bool = False
    governance_decision: str = "PENDING"
    findings: list[UIRepairPRFinding] = field(default_factory=list)


@dataclass
class UIRepairPRFinding:
    finding_id: str
    review_id: str
    severity: str # info | warning | error | critical
    category: str # security | quality | logic | style
    message: str
    file_path: str | None = None
    line_number: int | None = None
    suggestion: str | None = None


def to_plain_data(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_plain_data(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_plain_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain_data(item) for item in value]
    return value
