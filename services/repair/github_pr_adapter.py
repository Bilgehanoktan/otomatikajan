from __future__ import annotations

from pathlib import Path
from typing import Any

from services.repair.repair_models import RepairCandidate, RepairCase, RepairDecision, to_plain_data
from services.taskflow.taskflow_artifacts import write_json_artifact


def _slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    return "-".join(part for part in cleaned.split("-") if part)[:80] or "repair"


def prepare_draft_pr(context: dict[str, Any]) -> dict[str, Any]:
    repair_case: RepairCase = context["repair_case"]
    candidate: RepairCandidate = context["repair_candidate"]
    risk_decision: RepairDecision = context["risk_decision"]
    branch_name = f"codex/repair-{_slug(repair_case.incident_id)}"
    payload = {
        "dry_run": True,
        "branch_name": branch_name,
        "title": f"fix: repair {repair_case.incident_id}",
        "body": "\n".join(
            [
                "## Summary",
                repair_case.summary or "Self-repair candidate prepared.",
                "",
                "## Changed files",
                *[f"- {path}" for path in candidate.changed_files],
                "",
                "## Risk decision",
                f"- status: {risk_decision.status}",
                f"- risk_score: {risk_decision.risk_score}",
                f"- recommended_action: {risk_decision.recommended_action}",
            ]
        ),
        "changed_files": candidate.changed_files,
        "risk_decision": to_plain_data(risk_decision),
    }
    artifact = write_json_artifact(
        repair_case.incident_id,
        "prepare_draft_pr",
        "draft_pr.json",
        payload,
        output_root=context.get("output_root"),
    )
    return {"draft_pr": payload, "artifact_path": artifact.path, "artifact_type": "json"}

