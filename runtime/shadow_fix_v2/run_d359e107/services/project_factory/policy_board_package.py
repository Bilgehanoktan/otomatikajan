from typing import Dict, Any, Optional
from services.project_factory.models import PolicyProposalCollection, PolicyBoardPackage
from services.project_factory.artifacts import load_policy_proposals, write_policy_board_package

def generate_policy_board_package(workspace_root: Optional[str] = None) -> Dict[str, Any]:
    data = load_policy_proposals(workspace_root)
    if not data:
        raise ValueError("No policy proposals found.")
        
    col = PolicyProposalCollection(**data)
    
    approved = sum(1 for p in col.proposals if p.status == "POLICY_BOARD_APPROVED_FOR_PREVIEW")
    preview_ready = sum(1 for p in col.proposals if p.status == "POLICY_APPLY_PREVIEW_READY")
    blocked = sum(1 for p in col.proposals if p.status == "POLICY_BOARD_REJECTED" or p.status == "POLICY_APPLY_PREVIEW_BLOCKED")
    
    pkg = PolicyBoardPackage(
        proposal_count=len(col.proposals),
        approved_for_preview=approved,
        preview_ready=preview_ready,
        blocked=blocked
    )
    
    write_policy_board_package(pkg.model_dump(), workspace_root)
    
    return pkg.model_dump()
