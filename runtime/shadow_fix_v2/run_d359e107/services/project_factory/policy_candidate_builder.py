import uuid
from typing import List, Optional
from services.project_factory.models import PolicyProposal, RecommendedChange
from services.project_factory.artifacts import load_portfolio_intelligence, write_policy_suggestion_candidates

def build_policy_candidates(workspace_root: Optional[str] = None) -> List[PolicyProposal]:
    intel_data = load_portfolio_intelligence(workspace_root)
    if not intel_data:
        raise ValueError("No portfolio intelligence found. Cannot build policy candidates.")
    
    recommendations = intel_data.get("learning_recommendations", [])
    proposals = []
    
    for rec in recommendations:
        rec_id = rec.get("recommendation_id", "")
        title = rec.get("title", "Untitled Policy Fix")
        priority = rec.get("priority", "MEDIUM")
        target = rec.get("target", "")
        
        # Security Guard: target_files workspace dışına çıkamaz.
        if ".." in target or target.startswith("/"):
            continue # skip invalid targets
            
        # Example mapping from learning signal to policy change
        # Here we just generate a generic change based on the recommendation
        changes = []
        if "forbidden_action" in title.lower() or "direct_git_push" in title.lower() or "configs/external_project_agent_matrix.yaml" in target:
            changes.append(RecommendedChange(
                field="forbidden_actions",
                add=["direct_git_push", "bypass_human_gate"]
            ))
        else:
            changes.append(RecommendedChange(
                field="general_security_policy",
                update={"harden": True}
            ))
            
        proposals.append(PolicyProposal(
            proposal_id=f"POL-PF-{str(uuid.uuid4())[:8].upper()}",
            title=title,
            description=f"Generated from learning recommendation {rec_id}.",
            target_files=[target],
            proposal_type="policy_hardening",
            risk_level=priority,
            priority=priority,
            recommended_changes=changes,
            status="POLICY_SUGGESTIONS_READY",
            requires_human_gate=True,
            auto_apply_allowed=False  # strictly false
        ))
        
    write_policy_suggestion_candidates({
        "candidates": [p.model_dump() for p in proposals]
    }, workspace_root)
    
    return proposals
