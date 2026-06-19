from __future__ import annotations

from services.repair.path_policy import is_forbidden_path
from services.repair.repair_models import HIGH_RISK_PATH_MARKERS, RepairCandidate, RepairCase, RepairDecision


def _path_risk(path: str, forbidden_paths: list[str]) -> tuple[float, str]:
    normalized = path.replace("\\", "/").lower()
    if is_forbidden_path(normalized, forbidden_paths):
        return 0.95, "forbidden path"
    if any(marker in normalized for marker in HIGH_RISK_PATH_MARKERS):
        return 0.85, "high risk path marker"
    if normalized.startswith("tests/") or normalized.endswith((".md", ".rst", ".txt")):
        return 0.15, "test or documentation change"
    if "ui" in normalized or normalized.startswith("apps/"):
        return 0.28, "small UI/application surface"
    if normalized.startswith("services/") or normalized.startswith("libs/"):
        return 0.5, "service or library logic"
    return 0.35, "general code change"


def calculate_risk(repair_case: RepairCase, candidate: RepairCandidate, verifier_result: dict | None = None) -> RepairDecision:
    verifier_result = verifier_result or {}
    changed_files = candidate.changed_files or []

    if not changed_files:
        score = 0.2
        reason = "No files changed by Phase 1-3 mock candidate."
    else:
        risks = [_path_risk(path, repair_case.forbidden_paths) for path in changed_files]
        score = max(score for score, _ in risks)
        reason = "; ".join(f"{path}: {why}" for path, (_, why) in zip(changed_files, risks))

    if verifier_result.get("status") == "VERIFIER_FAILED":
        score = max(score, 0.61)
        reason = f"{reason}; verifier failed"
    joycode = verifier_result.get("joycode") or {}
    if joycode.get("failure_attribution") == "empty_patch":
        score = max(score, 0.61)
        reason = f"{reason}; empty patch"
    if joycode.get("failure_attribution") == "test_suppression_risk":
        score = max(score, 0.81)
        reason = f"{reason}; patch only changes tests"

    if score <= 0.30:
        status = "DRAFT_PR_READY"
        action = "DRAFT_PR_ALLOWED"
        level = "LOW"
    elif score <= 0.60:
        status = "HUMAN_APPROVAL_REQUIRED"
        action = "HUMAN_APPROVAL_REQUIRED"
        level = "MEDIUM"
    elif score <= 0.80:
        status = "QUORUM_REQUIRED"
        action = "QUORUM_REQUIRED"
        level = "HIGH"
    else:
        status = "AUTO_REPAIR_BLOCKED"
        action = "Manual senior review required"
        level = "CRITICAL"

    return RepairDecision(
        status=status,
        risk_score=round(score, 2),
        risk_level=level,
        recommended_action=action,
        reason=reason,
    )
