from __future__ import annotations

import hashlib

from services.repair.repair_models import RepairCase, RepairPlan


DEFAULT_FORBIDDEN_ACTIONS = [
    "Do not read .env or secrets.",
    "Do not modify auth, governance, config, migration, deployment, or infra files.",
    "Do not commit, push, merge, or touch production/main branch.",
    "Do not bypass tests, approval gates, or constitutional guardrails.",
]


def build_repair_plan(repair_case: RepairCase, suspected_files: list[dict] | None = None) -> RepairPlan:
    files = [str(item.get("file")) for item in suspected_files or [] if item.get("file")]
    if not files:
        files = list(repair_case.suspected_files)
    expected_tests = [repair_case.failed_command] if repair_case.failed_command else []
    root_cause = repair_case.summary or repair_case.traceback[:240] or "Repair case requires investigation."
    digest = hashlib.sha256(f"{repair_case.incident_id}:{root_cause}:{files}".encode("utf-8")).hexdigest()[:12]
    confidence = 0.65 if files else 0.25
    return RepairPlan(
        repair_plan_id=f"RP-{digest}",
        incident_id=repair_case.incident_id,
        root_cause_hypothesis=root_cause,
        target_files=files[:10],
        expected_fix_type="minimal_safe_patch",
        expected_tests=expected_tests,
        forbidden_actions=list(DEFAULT_FORBIDDEN_ACTIONS),
        rollback_strategy="Discard sandbox workspace or close draft PR without merge.",
        confidence=confidence,
    )

