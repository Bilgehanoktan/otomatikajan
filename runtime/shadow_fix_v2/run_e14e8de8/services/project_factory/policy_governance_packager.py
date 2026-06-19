import os
import shutil
from typing import Dict, Any
from pathlib import Path
from services.project_factory.models import PolicyGovernanceManifest
from services.project_factory.artifacts import (
    _resolve_policy_autopilot_dir,
    load_policy_draft_pr_plan,
    write_policy_governance_manifest
)
from services.project_factory.policy_pr_diff_summary import build_policy_pr_diff_summary
from services.project_factory.artifacts import load_policy_apply_preview

def generate_governance_evidence_pack(proposal_id: str, workspace_root: str = None) -> Dict[str, Any]:
    """
    Creates the policy_governance_evidence_pack directory and copies all relevant evidence files.
    Generates policy_governance_manifest.json and policy_pr_diff_summary.md inside it.
    """
    d = _resolve_policy_autopilot_dir(workspace_root, proposal_id)
    pack_dir = d / "policy_governance_evidence_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    
    plan = load_policy_draft_pr_plan(proposal_id, workspace_root)
    if not plan or plan.get("proposal_id") != proposal_id:
        raise ValueError("Policy Draft PR Plan not found or mismatch.")
        
    preview = load_policy_apply_preview(proposal_id, workspace_root)
    if not preview:
        raise ValueError("Apply preview not found.")
        
    evidence_files = [
        "policy_proposals.json",
        "policy_impact_analysis.json",
        "policy_risk_assessment.json",
        "policy_apply_preview.json",
        "policy_diff_summary.md",
        "policy_board_decisions.jsonl",
        "policy_board_package.json",
        "policy_draft_pr_plan.json"
    ]
    
    evidence_count = 0
    for file_name in evidence_files:
        src = d / file_name
        dst = pack_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)
            evidence_count += 1
            
    # Generate diff summary markdown
    diff_summary_content = build_policy_pr_diff_summary(plan, preview)
    with open(pack_dir / "policy_pr_diff_summary.md", "w", encoding="utf-8") as f:
        f.write(diff_summary_content)
    evidence_count += 1
        
    manifest = PolicyGovernanceManifest(
        proposal_id=proposal_id,
        evidence_count=evidence_count
    )
    
    manifest_dict = manifest.model_dump()
    write_policy_governance_manifest(proposal_id, manifest_dict, workspace_root)
    
    return manifest_dict
