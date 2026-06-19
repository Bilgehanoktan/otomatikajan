from typing import Dict, Any, Optional
from services.project_factory.models import RunPolicyAutopilotRequest, PolicyProposalDecisionRequest
from services.project_factory.policy_candidate_builder import build_policy_candidates
from services.project_factory.policy_impact_analyzer import analyze_policy_impact
from services.project_factory.policy_risk_assessor import assess_policy_risk
from services.project_factory.policy_proposal_writer import compile_policy_proposals, update_proposal_status
from services.project_factory.policy_autopilot_logs import log_policy_autopilot_event
from services.project_factory.artifacts import load_policy_proposals

def run_policy_autopilot(request: RunPolicyAutopilotRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    # 1. Build candidates
    candidates = build_policy_candidates(workspace_root)
    
    # 2. Analyze impact
    impacts = analyze_policy_impact(candidates, workspace_root)
    
    # 3. Assess risk
    assessments = assess_policy_risk(candidates, workspace_root)
    
    # 4. Compile proposals
    col = compile_policy_proposals(candidates, workspace_root)
    
    # 5. Log
    log_policy_autopilot_event(
        action="RUN_POLICY_AUTOPILOT",
        operator_id=request.operator_id,
        rationale=request.rationale,
        details={
            "candidates_count": len(candidates)
        },
        workspace_root=workspace_root
    )
    
    return {
        "status": "success",
        "proposals": col.model_dump()
    }

def get_policy_autopilot_data(workspace_root: Optional[str] = None) -> Dict[str, Any]:
    proposals = load_policy_proposals(workspace_root)
    if not proposals:
        return {"status": "success", "proposals": []}
    return {"status": "success", "proposals": proposals.get("proposals", [])}

def approve_for_policy_board(proposal_id: str, request: PolicyProposalDecisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    if not request.risk_acknowledgement:
        raise ValueError("Must acknowledge risks to approve for policy board.")
        
    prop = update_proposal_status(proposal_id, "POLICY_PROPOSAL_APPROVED_FOR_BOARD", workspace_root)
    
    log_policy_autopilot_event(
        action="APPROVE_FOR_POLICY_BOARD",
        operator_id=request.operator_id,
        rationale=request.rationale,
        details={"proposal_id": proposal_id},
        workspace_root=workspace_root
    )
    
    return {"status": "success", "proposal": prop.model_dump()}

def defer_policy_proposal(proposal_id: str, request: PolicyProposalDecisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    prop = update_proposal_status(proposal_id, "POLICY_PROPOSAL_DEFERRED", workspace_root)
    
    log_policy_autopilot_event(
        action="DEFER_POLICY_PROPOSAL",
        operator_id=request.operator_id,
        rationale=request.rationale,
        details={"proposal_id": proposal_id},
        workspace_root=workspace_root
    )
    
    return {"status": "success", "proposal": prop.model_dump()}

def reject_policy_proposal(proposal_id: str, request: PolicyProposalDecisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    prop = update_proposal_status(proposal_id, "POLICY_PROPOSAL_REJECTED", workspace_root)
    
    log_policy_autopilot_event(
        action="REJECT_POLICY_PROPOSAL",
        operator_id=request.operator_id,
        rationale=request.rationale,
        details={"proposal_id": proposal_id},
        workspace_root=workspace_root
    )
    
    return {"status": "success", "proposal": prop.model_dump()}
