from typing import List, Any
from services.project_factory.models import PolicyProposal

def check_policy_safety(proposal: PolicyProposal) -> List[str]:
    blocking_risks = []
    
    if proposal.auto_apply_allowed:
        blocking_risks.append("auto_apply_allowed must be false.")
        
    for f in proposal.target_files:
        if ".." in f or f.startswith("/"):
            blocking_risks.append(f"Target file {f} is out of workspace bounds.")
        if ".env" in f or "secret" in f.lower() or "key" in f.lower() or "db" in f.lower():
            blocking_risks.append(f"Target file {f} contains sensitive paths (.env, secret, key, db).")
            
    for rc in proposal.recommended_changes:
        if rc.remove:
            blocking_risks.append("Delete operations are blocked in recommended_changes.")
            
    return blocking_risks
