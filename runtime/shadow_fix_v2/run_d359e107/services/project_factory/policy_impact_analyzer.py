from typing import List, Optional
from services.project_factory.models import PolicyProposal, PolicyImpactAnalysis
from services.project_factory.artifacts import write_policy_impact_analysis

def analyze_policy_impact(candidates: List[PolicyProposal], workspace_root: Optional[str] = None) -> List[PolicyImpactAnalysis]:
    impacts = []
    
    for c in candidates:
        affected_agents = []
        benefit = ""
        side_effects = []
        
        # simple heuristic
        for t in c.target_files:
            if "external_project_agent_matrix" in t:
                affected_agents.extend(["openhands", "openhands_sdk", "mini_swe_agent"])
                benefit = "Blocks direct git push and Human Gate bypass patterns."
                side_effects.append("Some external adapters may require explicit approval metadata.")
            else:
                affected_agents.append("all_agents")
                benefit = "General security posture improvement."
                side_effects.append("May slow down automated tasks due to stricter rules.")
                
        impact = PolicyImpactAnalysis(
            proposal_id=c.proposal_id,
            target_files=c.target_files,
            affected_agents=list(set(affected_agents)),
            expected_benefit=benefit,
            potential_side_effects=side_effects,
            rollback_plan_required=True
        )
        impacts.append(impact)
        
    write_policy_impact_analysis({
        "impacts": [i.model_dump() for i in impacts]
    }, workspace_root)
    
    return impacts
