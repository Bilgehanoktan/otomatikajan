from __future__ import annotations

from typing import Dict, Any, Optional

from services.project_factory.artifacts import load_apply_preview, write_draft_pr_plan, load_draft_pr_plan
from services.project_factory.models import DraftPrPrepareRequest, DraftPrPlan
from services.project_factory.pr_plan_logs import log_draft_pr_plan


def prepare_draft_pr_plan(
    project_id: str,
    request: DraftPrPrepareRequest,
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    if not request.risk_acknowledgement:
        raise ValueError("risk_acknowledgement is required to prepare draft PR plan.")
    if request.target_branch not in ["main", "master"]:
        raise ValueError("target_branch must be main or master.")

    preview = load_apply_preview(project_id, workspace_root)
    if not preview:
        raise ValueError("Missing apply_preview.json. Run apply-preview first.")
    if preview.get("production_apply_performed", True) is not False:
        raise ValueError("apply_preview.production_apply_performed must be False.")
    if preview.get("blocking_risks"):
        log_draft_pr_plan(
            project_id,
            "PREPARE_DRAFT_PR_PLAN_BLOCKED",
            request.operator_id,
            "Blocked by apply_preview blocking risks",
            "PR_PREPARATION_REJECTED",
            workspace_root,
        )
        raise ValueError(f"Cannot prepare draft PR plan with blocking risks: {preview.get('blocking_risks')}")

    files_to_apply = [change["path"] for change in preview.get("file_changes", [])]
    plan = DraftPrPlan(
        project_id=project_id,
        status="DRAFT_PR_PLAN_READY",
        branch_name=f"codex/project-factory-{project_id}",
        target_branch=request.target_branch,
        draft_title=request.draft_title,
        draft_body=(
            f"Draft PR plan for Project Factory delivery `{project_id}`.\n\n"
            "No git operations were performed by this planning step."
        ),
        files_to_apply=files_to_apply,
        apply_preview_ref="apply_preview.json",
        requires_operator_confirmation=True,
        git_operations_performed=False,
    )
    plan_dict = plan.model_dump()
    write_draft_pr_plan(project_id, plan_dict, workspace_root)
    log_draft_pr_plan(
        project_id,
        "PREPARE_DRAFT_PR_PLAN",
        request.operator_id,
        request.rationale,
        plan.status,
        workspace_root,
    )
    return plan_dict


def get_draft_pr_plan(project_id: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return load_draft_pr_plan(project_id, workspace_root)
