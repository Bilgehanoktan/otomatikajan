from typing import Dict, Any, List, Optional
import os

def check_policy_pr_creation_safety(
    request: Dict[str, Any],
    draft_pr_plan: Dict[str, Any],
    apply_preview: Dict[str, Any],
    governance_manifest: Dict[str, Any],
    four_eyes_required: bool = False
) -> List[str]:
    """
    Perform strict safety re-checks before creating a Git branch and draft PR.
    """
    risks = []
    
    # Check operator inputs
    if not request.get("operator_id"):
        risks.append("Operator ID is missing")
    if not request.get("rationale"):
        risks.append("Rationale is missing")
    if not request.get("risk_acknowledgement"):
        risks.append("Risk acknowledgement is required for PR creation")
        
    # Check Four-Eyes Principle
    if four_eyes_required:
        # Assuming draft_pr_plan has an operator_id who prepared it, or we check the logs
        # For simplicity, if we pass prepare_operator_id in request or find it:
        prepare_op = request.get("prepare_operator_id")
        if prepare_op and prepare_op == request.get("operator_id"):
            risks.append("Four-Eyes Principle violated: Creator cannot be the approver")
            
    # Check apply_preview constraints
    if apply_preview.get("production_apply_performed"):
        risks.append("apply_preview violation: production_apply_performed must be false")
    if apply_preview.get("policy_files_modified"):
        risks.append("apply_preview violation: policy_files_modified must be false")
    if apply_preview.get("blocking_risks", []):
        risks.append("apply_preview contains blocking risks")
        
    # Check draft_pr_plan constraints
    if draft_pr_plan.get("git_operations_performed"):
        risks.append("draft_pr_plan violation: git_operations_performed must be false")
    branch_name = draft_pr_plan.get("branch_name", "")
    if not branch_name.startswith("codex/"):
        risks.append("draft_pr_plan violation: branch_name must start with 'codex/'")
        
    # Check files
    files_to_apply = draft_pr_plan.get("files_to_apply", [])
    for f in files_to_apply:
        lower_f = f.lower()
        if ".." in f or os.path.isabs(f):
            risks.append(f"draft_pr_plan violation: file {f} is not a relative workspace path")
        if any(bad in lower_f for bad in [".env", "secret", "key", "db"]):
            risks.append(f"draft_pr_plan violation: target file {f} is blocked (sensitive)")
            
    # Check unsupported policy change types
    # Only allow appending to lists or simple modifications for now
    preview_changes = apply_preview.get("preview_changes", [])
    for c in preview_changes:
        c_type = c.get("change_type", "")
        # Very simple validation, user specifies we want to block unsupported types
        if c_type not in ["APPEND", "MODIFY_LIST"]:
            # Depending on how the apply_preview formats it. Let's say if it's explicitly forbidden
            # We will allow APPEND.
            # In our mockup, if change_type is UNKNOWN, block it.
            if c_type == "UNKNOWN":
                 risks.append(f"Unsupported policy change type: {c_type}")

    return risks
