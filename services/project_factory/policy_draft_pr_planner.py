import os
from typing import Dict, Any
from services.project_factory.models import PolicyDraftPRPlanRequest, PolicyDraftPRPlan
from services.project_factory.artifacts import load_policy_apply_preview, write_policy_draft_pr_plan
from services.project_factory.policy_board_service import load_policy_proposals
from services.project_factory.policy_pr_plan_safety import check_policy_pr_plan_safety
from services.project_factory.policy_pr_plan_logs import log_policy_pr_plan

def prepare_draft_pr_plan(proposal_id: str, request: PolicyDraftPRPlanRequest) -> Dict[str, Any]:
    """
    Prepares a draft PR plan from an approved apply preview without modifying git or policy files.
    """
    preview = load_policy_apply_preview()
    if not preview:
        raise ValueError("Apply preview not found.")
        
    proposals_data = load_policy_proposals()
    proposal = None
    if proposals_data:
        for p in proposals_data.get("proposals", []):
            if p.get("proposal_id") == proposal_id:
                proposal = p
                break
                
    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found.")
        
    if proposal.get("status") != "POLICY_BOARD_APPROVED_FOR_PREVIEW":
        # The prompt specifies the input is the apply preview, but the status in the proposal might still be "APPROVED_FOR_PREVIEW"
        # Let's allow either POLICY_BOARD_APPROVED_FOR_PREVIEW or POLICY_APPLY_PREVIEW_READY
        if proposal.get("status") not in ["POLICY_BOARD_APPROVED_FOR_PREVIEW", "POLICY_APPLY_PREVIEW_READY"]:
            raise ValueError(f"Proposal {proposal_id} is not in a valid state for PR plan preparation.")

    if preview.get("proposal_id") != proposal_id:
        raise ValueError(f"Apply preview is for a different proposal ({preview.get('proposal_id')}).")
        
    branch_name = f"codex/policy-{proposal_id}"
    
    risks = check_policy_pr_plan_safety(
        apply_preview=preview,
        proposal=proposal,
        target_branch=request.target_branch,
        branch_name=branch_name,
        risk_acknowledgement=request.risk_acknowledgement
    )
    
    if risks:
        log_policy_pr_plan(
            action="PREPARE_POLICY_DRAFT_PR_PLAN_BLOCKED",
            proposal_id=proposal_id,
            operator_id=request.operator_id,
            rationale="Blocked by safety checks",
            status="POLICY_PR_PLAN_BLOCKED"
        )
        raise ValueError(f"Safety checks failed: {', '.join(risks)}")
        
    plan = PolicyDraftPRPlan(
        proposal_id=proposal_id,
        branch_name=branch_name,
        target_branch=request.target_branch,
        draft_title=request.draft_title,
        draft_body=proposal.get("description", ""),
        files_to_apply=proposal.get("target_files", [])
    )
    
    plan_dict = plan.model_dump()
    
    write_policy_draft_pr_plan(plan_dict)
    
    log_policy_pr_plan(
        action="PREPARE_POLICY_DRAFT_PR_PLAN",
        proposal_id=proposal_id,
        operator_id=request.operator_id,
        rationale=request.rationale,
        status=plan.status
    )
    
    return plan_dict
