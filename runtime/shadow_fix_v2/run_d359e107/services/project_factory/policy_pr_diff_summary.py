import os
from typing import Dict, Any

def build_policy_pr_diff_summary(plan: Dict[str, Any], preview: Dict[str, Any]) -> str:
    """
    Builds a markdown summary for the Policy Draft PR Plan.
    """
    md = [
        f"# Policy Draft PR Plan: {plan.get('draft_title', 'Untitled')}",
        "",
        f"**Proposal ID:** `{plan.get('proposal_id')}`",
        f"**Branch Name:** `{plan.get('branch_name')}`",
        f"**Target Branch:** `{plan.get('target_branch')}`",
        f"**Status:** `{plan.get('status')}`",
        "",
        "## Description",
        plan.get("draft_body", "No description provided."),
        "",
        "## Guardrails",
        f"- Git Operations Performed: **{plan.get('git_operations_performed')}**",
        f"- Policy Files Modified: **{plan.get('policy_files_modified')}**",
        f"- Production Apply Performed: **{preview.get('production_apply_performed', False)}**",
        "",
        "## Files to Apply"
    ]
    
    files = plan.get("files_to_apply", [])
    if not files:
        md.append("- No files targeted")
    else:
        for f in files:
            md.append(f"- `{f}`")
            
    md.extend([
        "",
        "## Preview Summary",
        f"- Risk Level: {preview.get('preview_summary', {}).get('risk_level', 'UNKNOWN')}",
        f"- Total Changes: {preview.get('preview_summary', {}).get('total_changes', 0)}",
        f"- Requires Human Gate: {preview.get('preview_summary', {}).get('requires_human_gate', True)}"
    ])
    
    return "\n".join(md)
