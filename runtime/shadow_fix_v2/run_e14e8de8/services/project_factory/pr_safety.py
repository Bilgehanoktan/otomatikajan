from __future__ import annotations

from pathlib import PurePosixPath
from typing import Dict, Any, Optional
from services.project_factory.artifacts import load_apply_preview, load_draft_pr_plan
from services.project_factory.delivery_packager import load_delivery_manifest

def validate_pr_creation_safety(
    project_id: str,
    operator_id: str,
    rationale: str,
    risk_acknowledgement: bool,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates that a Draft PR can be safely created without violating production safety.
    Raises ValueError if any safety constraint is violated.
    Returns parsed configurations.
    """
    # 1. Basic auth & rationale checks
    if not operator_id or len(operator_id.strip()) == 0:
        raise ValueError("operator_id is required to create a draft PR.")
    if not rationale or len(rationale.strip()) < 5:
        raise ValueError("A valid rationale (min 5 chars) is required.")
    if not risk_acknowledgement:
        raise ValueError("Operator must acknowledge risks (risk_acknowledgement=true).")

    # 2. Check underlying delivery manifest for locks
    delivery_manifest = load_delivery_manifest(project_id, workspace_root)
    if not delivery_manifest:
        raise ValueError(f"No delivery_manifest found for {project_id}.")
    
    if delivery_manifest.get("production_apply_allowed", True) is not False:
        raise ValueError("Safety violation: delivery_manifest.production_apply_allowed must strictly be False.")

    # 3. Check apply_preview
    apply_preview = load_apply_preview(project_id, workspace_root)
    if not apply_preview:
        raise ValueError("Missing apply_preview.json. Cannot create PR without a prior dry-run preview.")
    
    blocking_risks = apply_preview.get("blocking_risks", [])
    if blocking_risks and len(blocking_risks) > 0:
        raise ValueError(f"Cannot create PR: apply_preview contains blocking risks: {blocking_risks}")

    if apply_preview.get("production_apply_performed", True) is not False:
        raise ValueError("Safety violation: apply_preview indicates production apply was already performed.")

    # 4. Check draft_pr_plan
    pr_plan = load_draft_pr_plan(project_id, workspace_root)
    if not pr_plan:
        raise ValueError("Missing draft_pr_plan.json. Cannot create PR without an approved plan.")

    branch_name = pr_plan.get("branch_name", "")
    if not branch_name.startswith("codex/"):
        raise ValueError(f"Safety violation: branch_name must start with 'codex/'. Found: {branch_name}")
    
    if pr_plan.get("target_branch", "") not in ["main", "master"]:
        raise ValueError("Safety violation: target_branch must be main or master.")

    forbidden_keywords = [".env", "secret", "credentials", ".pem", ".key", ".p12", ".db"]
    for file_path in pr_plan.get("files_to_apply", []):
        normalized = str(file_path).replace("\\", "/")
        path = PurePosixPath(normalized)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Safety violation: files_to_apply contains path traversal: {file_path}")
        lowered = normalized.lower()
        if any(keyword in lowered for keyword in forbidden_keywords):
            raise ValueError(f"Safety violation: files_to_apply contains protected file: {file_path}")

    return {
        "delivery_manifest": delivery_manifest,
        "apply_preview": apply_preview,
        "draft_pr_plan": pr_plan
    }
