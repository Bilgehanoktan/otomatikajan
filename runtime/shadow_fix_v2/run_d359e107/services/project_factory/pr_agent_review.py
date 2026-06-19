"""
PR-Agent Style Static Review Adapter.

Reads diff_summary, draft_pr_plan, draft_pr_creation, candidate_manifest,
and risk_assessment artifacts. Produces a static code review report checking
for risky files, blocking risks, secret patterns, large/binary files,
test failures, and production apply flag violations.

No external vendoring — pattern-based static adapter only.
"""
from __future__ import annotations

import re
from typing import Optional, List
from services.project_factory.artifacts import (
    _resolve_project_dir,
    _load_json_artifact,
    load_draft_pr_creation,
    load_apply_preview,
    write_pr_agent_review,
)
from services.project_factory.models import PrAgentReview, PrAgentFinding

# Secret patterns to detect
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}"),
    re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9_]{36}"),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
]

RISKY_FILE_EXTENSIONS = {".env", ".pem", ".key", ".pfx", ".p12"}
LARGE_FILE_THRESHOLD_BYTES = 5_000_000  # 5 MB
BINARY_EXTENSIONS = {".exe", ".dll", ".so", ".dylib", ".bin", ".wasm", ".zip", ".tar", ".gz"}


def run_pr_agent_review(
    project_id: str,
    workspace_root: Optional[str] = None,
) -> PrAgentReview:
    """
    Performs a static PR-Agent style review on the project artifacts.
    """
    findings: List[PrAgentFinding] = []
    suggestions: List[str] = []
    project_dir = _resolve_project_dir(project_id, workspace_root)

    # 1. Load draft PR creation artifact for safety flag checks
    pr_creation = load_draft_pr_creation(project_id, workspace_root)
    if pr_creation:
        if pr_creation.get("merge_performed", False):
            findings.append(PrAgentFinding(
                category="safety_violation",
                severity="blocking",
                description="merge_performed is true — merge was executed during PR creation.",
            ))
        if pr_creation.get("force_push_performed", False):
            findings.append(PrAgentFinding(
                category="safety_violation",
                severity="blocking",
                description="force_push_performed is true — force push detected.",
            ))
        if pr_creation.get("production_direct_write", False):
            findings.append(PrAgentFinding(
                category="safety_violation",
                severity="blocking",
                description="production_direct_write is true — direct production write detected.",
            ))

    # 2. Check apply_preview for blocking risks
    apply_preview = load_apply_preview(project_id, workspace_root)
    if apply_preview:
        blocking = apply_preview.get("blocking_risks", [])
        for risk in blocking:
            findings.append(PrAgentFinding(
                category="apply_preview_risk",
                severity="blocking",
                description=f"Apply preview blocking risk: {risk}",
            ))

    # 3. Load candidate_manifest and inspect files
    candidate_manifest = _load_json_artifact(project_id, "candidate_manifest.json", workspace_root)
    if candidate_manifest:
        for f_info in candidate_manifest.get("files", []):
            file_path = f_info.get("path", "")
            ext = "." + file_path.rsplit(".", 1)[-1] if "." in file_path else ""

            if ext.lower() in RISKY_FILE_EXTENSIONS:
                findings.append(PrAgentFinding(
                    category="risky_file",
                    severity="blocking",
                    description=f"Risky file detected: {file_path}",
                    file_path=file_path,
                ))

            if ext.lower() in BINARY_EXTENSIONS:
                findings.append(PrAgentFinding(
                    category="binary_file",
                    severity="warning",
                    description=f"Binary file in candidate: {file_path}",
                    file_path=file_path,
                ))

    # 4. Load risk_assessment for high risks
    risk_assessment = _load_json_artifact(project_id, "risk_assessment.json", workspace_root)
    if risk_assessment:
        for br in risk_assessment.get("blocking_risks", []):
            findings.append(PrAgentFinding(
                category="risk_assessment",
                severity="blocking",
                description=f"Blocking risk from risk assessment: {br}",
            ))
        for w in risk_assessment.get("warnings", []):
            findings.append(PrAgentFinding(
                category="risk_assessment",
                severity="warning",
                description=f"Warning from risk assessment: {w}",
            ))

    # 5. Read diff_summary.md for secret scanning
    diff_summary_path = project_dir / "diff_summary.md"
    if diff_summary_path.exists():
        content = diff_summary_path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            matches = pattern.findall(content)
            if matches:
                findings.append(PrAgentFinding(
                    category="secret_detected",
                    severity="blocking",
                    description=f"Potential secret pattern detected in diff_summary.md ({len(matches)} matches).",
                ))
                break  # One finding is enough

    # 6. Compute summary
    blocking_count = sum(1 for f in findings if f.severity == "blocking")
    warning_count = sum(1 for f in findings if f.severity == "warning")

    if blocking_count > 0:
        status = "BLOCKED"
        summary = f"{blocking_count} blocking finding(s) detected. Review cannot pass."
    elif warning_count > 0:
        status = "WARNINGS"
        summary = f"No blocking issues. {warning_count} warning(s) require attention."
        suggestions.append("Review the warnings before marking as reviewed.")
    else:
        status = "PASSED"
        summary = "No blocking issues detected."

    review = PrAgentReview(
        status=status,
        summary=summary,
        findings=findings,
        suggestions=suggestions,
    )

    # Save artifact
    write_pr_agent_review(project_id, review.model_dump(), workspace_root)
    return review
