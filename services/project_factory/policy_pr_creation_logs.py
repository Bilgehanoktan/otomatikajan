import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

def log_policy_pr_creation(
    action: str,
    proposal_id: str,
    operator_id: str,
    rationale: str,
    status: str,
    branch_name: Optional[str] = None,
    commit_sha: Optional[str] = None,
    pr_url: Optional[str] = None,
    reason: Optional[str] = None,
    workspace_root: Optional[str] = None
) -> None:
    """
    Append-only log for Phase 18 - Operator-Approved Policy Draft PR Creation.
    """
    d = _resolve_policy_autopilot_dir(workspace_root)
    log_file = d / "policy_pr_creation_logs.jsonl"
    
    # Use timezone-aware datetime per deprecation warnings
    try:
        from datetime import timezone
        created_at = datetime.now(timezone.utc).isoformat()
    except Exception:
        created_at = datetime.utcnow().isoformat() + "Z"
        
    entry = {
        "event_id": f"PRCREATE-{str(uuid.uuid4())[:8]}",
        "action": action,
        "proposal_id": proposal_id,
        "operator_id": operator_id,
        "rationale": rationale,
        "status": status,
        "branch_name": branch_name,
        "commit_sha": commit_sha,
        "pr_url": pr_url,
        "reason": reason,
        "created_at": created_at
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_policy_pr_creation_logs(workspace_root: Optional[str] = None) -> List[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    log_file = d / "policy_pr_creation_logs.jsonl"
    
    if not log_file.exists():
        return []
        
    logs = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except Exception:
                    pass
    return logs
