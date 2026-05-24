from pathlib import PurePosixPath, PureWindowsPath
from typing import List, Any
from services.project_factory.models import PolicyProposal

def _is_workspace_relative_path(path: str) -> bool:
    posix_path = PurePosixPath(path.replace("\\", "/"))
    windows_path = PureWindowsPath(path)
    if posix_path.is_absolute() or windows_path.drive or windows_path.root:
        return False
    return ".." not in posix_path.parts

def check_policy_safety(proposal: PolicyProposal) -> List[str]:
    blocking_risks = []
    
    if proposal.auto_apply_allowed:
        blocking_risks.append("auto_apply_allowed must be false.")
        
    for f in proposal.target_files:
        if not _is_workspace_relative_path(f):
            blocking_risks.append(f"Target file {f} is out of workspace bounds.")
        lower_f = f.lower()
        if ".env" in lower_f or "secret" in lower_f or "key" in lower_f or "db" in lower_f:
            blocking_risks.append(f"Target file {f} contains sensitive paths (.env, secret, key, db).")
            
    for rc in proposal.recommended_changes:
        if rc.remove:
            blocking_risks.append("Delete operations are blocked in recommended_changes.")
            
    return blocking_risks
\n# Added via Policy Autopilot SMOKE-TEST-001\n