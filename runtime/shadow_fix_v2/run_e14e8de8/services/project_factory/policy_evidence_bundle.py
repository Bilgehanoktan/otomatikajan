import shutil
import os
from pathlib import Path
from typing import Optional
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

def build_policy_evidence_bundle(archive_dir: Path, workspace_root: Optional[str] = None, proposal_id: Optional[str] = None) -> int:
    """
    Copies all governance and policy artifacts into the evidence bundle.
    Returns the number of files bundled.
    """
    source_dir = _resolve_policy_autopilot_dir(workspace_root, proposal_id)
    bundle_dir = archive_dir / "policy_evidence_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    artifacts_to_bundle = [
        "policy_proposals.json",
        "policy_impact_analysis.json",
        "policy_risk_assessment.json",
        "policy_board_decisions.jsonl",
        "policy_apply_preview.json",
        "policy_diff_summary.md",
        "policy_board_package.json",
        "policy_draft_pr_plan.json",
        "policy_pr_creation.json",
        "policy_pr_status.json",
        "policy_pr_creation_logs.jsonl",
        "policy_pr_review_report.json",
        "policy_pr_agent_review.json",
        "policy_verifier_mesh_report.json",
        "policy_pr_review_scorecard.json",
        "policy_pr_review_decisions.jsonl",
        "policy_final_decision_logs.jsonl"
    ]
    
    count = 0
    for file_name in artifacts_to_bundle:
        src = source_dir / file_name
        if src.exists() and src.is_file():
            shutil.copy2(src, bundle_dir / file_name)
            count += 1
            
    # Also bundle the governance pack if it exists
    gov_pack_dir = source_dir / "policy_governance_evidence_pack"
    if gov_pack_dir.exists() and gov_pack_dir.is_dir():
        for item in gov_pack_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, bundle_dir / item.name)
                count += 1
                
    return count
