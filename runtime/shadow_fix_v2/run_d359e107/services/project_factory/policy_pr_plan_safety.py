import os
from typing import Dict, Any, List
from pathlib import Path

def check_policy_pr_plan_safety(
    apply_preview: Dict[str, Any],
    proposal: Dict[str, Any],
    target_branch: str,
    branch_name: str,
    risk_acknowledgement: bool
) -> List[str]:
    """
    Validates safety constraints before preparing a Policy Draft PR Plan.
    Returns a list of blocking risks. If empty, it's safe to proceed.
    """
    risks = []
    
    # 1. Base requirements
    if not apply_preview:
        risks.append("apply_preview is missing. Cannot prepare plan.")
        return risks
        
    if not proposal:
        risks.append("policy proposal is missing. Cannot prepare plan.")
        return risks
        
    if not risk_acknowledgement:
        risks.append("risk_acknowledgement is required.")
        
    # 2. Preview constraints
    if apply_preview.get("production_apply_performed", False):
        risks.append("production_apply_performed must be false.")
        
    if apply_preview.get("policy_files_modified", False):
        risks.append("policy_files_modified must be false.")
        
    # 3. Branch constraints
    if not target_branch:
        risks.append("target_branch cannot be empty.")
        
    if not branch_name or not branch_name.startswith("codex/"):
        risks.append("branch_name must start with 'codex/'.")
        
    # 4. Proposal constraints
    if proposal.get("auto_apply_allowed", False):
        risks.append("auto_apply_allowed must be false for policy proposals.")
        
    if apply_preview.get("blocking_risks", []):
        risks.append("Apply preview contains blocking risks. Cannot proceed.")

    # 5. File constraints
    files_to_apply = proposal.get("target_files", [])
    workspace_root = os.getcwd()
    
    sensitive_files = {".env", "secret", "credentials", "db", "sqlite"}
    
    for f in files_to_apply:
        # Path traversal check
        try:
            full_path = Path(workspace_root) / f
            full_path.resolve().relative_to(Path(workspace_root).resolve())
        except ValueError:
            risks.append(f"File {f} is out of workspace bounds.")
            
        # Sensitive file check
        lower_f = f.lower()
        if any(s in lower_f for s in sensitive_files):
            risks.append(f"File {f} targets a sensitive area.")
            
    return risks
