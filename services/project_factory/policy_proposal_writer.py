from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from services.project_factory.models import PolicyProposal, PolicyProposalCollection
from services.project_factory.artifacts import write_policy_proposals, load_policy_proposals

def compile_policy_proposals(candidates: List[PolicyProposal], workspace_root: Optional[str] = None) -> PolicyProposalCollection:
    # At this step we just save the candidates into the final proposals file
    # Their status is already POLICY_SUGGESTIONS_READY
    
    col = PolicyProposalCollection(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="portfolio_intelligence",
        proposals=candidates
    )
    
    write_policy_proposals(col.model_dump(), workspace_root)
    return col

def update_proposal_status(proposal_id: str, new_status: str, workspace_root: Optional[str] = None) -> PolicyProposal:
    data = load_policy_proposals(workspace_root)
    if not data:
        raise ValueError("No policy proposals found.")
        
    col = PolicyProposalCollection(**data)
    
    updated_prop = None
    for p in col.proposals:
        if p.proposal_id == proposal_id:
            p.status = new_status
            updated_prop = p
            break
            
    if not updated_prop:
        raise ValueError(f"Proposal {proposal_id} not found.")
        
    write_policy_proposals(col.model_dump(), workspace_root)
    return updated_prop
