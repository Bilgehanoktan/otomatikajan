from typing import Dict, Any, Optional
from services.project_factory.models import PolicyBoardDecisionRequest, PolicyProposalCollection
from services.project_factory.artifacts import load_policy_proposals, write_policy_proposals
from services.project_factory.policy_board_logs import log_policy_board_decision
from services.project_factory.policy_safety import check_policy_safety

def _update_proposal_status(proposal_id: str, request: PolicyBoardDecisionRequest, action: str, new_status: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    data = load_policy_proposals(workspace_root)
    if not data:
        raise ValueError("No policy proposals found.")
        
    col = PolicyProposalCollection(**data)
    
    updated_prop = None
    for p in col.proposals:
        if p.proposal_id == proposal_id:
            # Safety Check
            blocking_risks = check_policy_safety(p)
            if blocking_risks:
                raise ValueError(f"Proposal {proposal_id} blocked by safety rules: {blocking_risks}")
                
            from_status = p.status
            p.status = new_status
            updated_prop = p
            break
            
    if not updated_prop:
        raise ValueError(f"Proposal {proposal_id} not found.")
        
    write_policy_proposals(col.model_dump(), workspace_root)
    
    log_policy_board_decision(
        proposal_id=proposal_id,
        action=action,
        from_status=from_status,
        to_status=new_status,
        operator_id=request.operator_id,
        rationale=request.rationale,
        risk_acknowledgement=request.risk_acknowledgement,
        workspace_root=workspace_root
    )
    
    return updated_prop.model_dump()

def approve_for_preview(proposal_id: str, request: PolicyBoardDecisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    if not request.risk_acknowledgement:
        raise ValueError("Must acknowledge risks to approve for preview.")
    return _update_proposal_status(proposal_id, request, "APPROVE_FOR_PREVIEW", "POLICY_BOARD_APPROVED_FOR_PREVIEW", workspace_root)

def request_revision(proposal_id: str, request: PolicyBoardDecisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    return _update_proposal_status(proposal_id, request, "REQUEST_REVISION", "POLICY_BOARD_REVISION_REQUESTED", workspace_root)

def reject_proposal(proposal_id: str, request: PolicyBoardDecisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    return _update_proposal_status(proposal_id, request, "REJECT", "POLICY_BOARD_REJECTED", workspace_root)
