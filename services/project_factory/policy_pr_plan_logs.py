import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

def log_policy_pr_plan(
    action: str,
    proposal_id: str,
    operator_id: str,
    rationale: str,
    status: str,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Append-only log for Policy Draft PR Plan preparation.
    """
    d = _resolve_policy_autopilot_dir(workspace_root)
    log_file = d / "policy_pr_plan_logs.jsonl"
    
    event = {
        "event_id": f"PPPLAN-{uuid.uuid4().hex[:8]}",
        "action": action,
        "proposal_id": proposal_id,
        "operator_id": operator_id,
        "rationale": rationale,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "git_operations_performed": False
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
    return event

def load_policy_pr_plan_logs(workspace_root: Optional[str] = None) -> List[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    log_file = d / "policy_pr_plan_logs.jsonl"
    if not log_file.exists():
        return []
        
    events = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events
