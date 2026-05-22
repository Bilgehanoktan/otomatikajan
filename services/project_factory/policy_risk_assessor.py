from typing import List, Optional
from services.project_factory.models import PolicyProposal, PolicyRiskAssessment
from services.project_factory.artifacts import write_policy_risk_assessment

def assess_policy_risk(candidates: List[PolicyProposal], workspace_root: Optional[str] = None) -> List[PolicyRiskAssessment]:
    assessments = []
    
    for c in candidates:
        risk_score = 0
        blocking = []
        warnings = []
        
        if c.risk_level == "HIGH":
            risk_score += 50
        elif c.risk_level == "MEDIUM":
            risk_score += 30
        else:
            risk_score += 10
            
        for f in c.target_files:
            if "external_project_agent_matrix" in f:
                warnings.append("Policy update may affect external agent adapters.")
                risk_score += 15
                
        # Security Guard: Must not auto-apply
        if c.auto_apply_allowed:
            blocking.append("auto_apply_allowed must be False for policy proposals.")
            risk_score = 100
            
        if not c.requires_human_gate:
            blocking.append("requires_human_gate must be True for policy proposals.")
            risk_score = 100
            
        decision = "APPROVE_FOR_POLICY_BOARD" if not blocking else "REJECT"
        
        ass = PolicyRiskAssessment(
            proposal_id=c.proposal_id,
            risk_score=risk_score,
            risk_level="HIGH" if risk_score > 60 else ("MEDIUM" if risk_score > 30 else "LOW"),
            blocking_risks=blocking,
            warnings=warnings,
            recommended_decision=decision
        )
        assessments.append(ass)
        
    write_policy_risk_assessment({
        "assessments": [a.model_dump() for a in assessments]
    }, workspace_root)
    
    return assessments
