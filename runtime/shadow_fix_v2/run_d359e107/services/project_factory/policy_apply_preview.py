from typing import Dict, Any, Optional
from services.project_factory.models import PolicyProposalCollection, PolicyApplyPreview, PreviewChange
from services.project_factory.artifacts import load_policy_proposals, write_policy_apply_preview
from services.project_factory.policy_diff_builder import build_policy_diff_summary
from services.project_factory.policy_safety import check_policy_safety

def generate_apply_preview(proposal_id: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    data = load_policy_proposals(workspace_root)
    if not data:
        raise ValueError("No policy proposals found.")
        
    col = PolicyProposalCollection(**data)
    
    target_prop = None
    for p in col.proposals:
        if p.proposal_id == proposal_id:
            target_prop = p
            break
            
    if not target_prop:
        raise ValueError(f"Proposal {proposal_id} not found.")
        
    if target_prop.status != "POLICY_BOARD_APPROVED_FOR_PREVIEW":
        raise ValueError(f"Proposal {proposal_id} must be APPROVED_FOR_PREVIEW to generate apply preview.")
        
    # Safety Check
    blocking_risks = check_policy_safety(target_prop)
    
    preview_changes = []
    for rc in target_prop.recommended_changes:
        for t in target_prop.target_files:
            preview_changes.append(PreviewChange(
                target_file=t,
                change_type="MODIFY",
                field=rc.field,
                add=rc.add,
                update=rc.update,
                risk=target_prop.risk_level
            ))
            
    preview = PolicyApplyPreview(
        proposal_id=proposal_id,
        status="POLICY_APPLY_PREVIEW_READY",
        production_apply_performed=False,
        policy_files_modified=False,
        target_files=target_prop.target_files,
        preview_changes=preview_changes,
        blocking_risks=blocking_risks
    )
    
    if blocking_risks:
        preview.status = "POLICY_APPLY_PREVIEW_BLOCKED"
        
    write_policy_apply_preview(proposal_id, preview.model_dump(), workspace_root)
    build_policy_diff_summary(preview, workspace_root)
    
    return preview.model_dump()
