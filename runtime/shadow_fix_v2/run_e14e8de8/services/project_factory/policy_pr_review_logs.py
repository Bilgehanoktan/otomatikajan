import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

def append_policy_pr_review_log(
    proposal_id: str,
    action: str,
    operator_id: str,
    details: Dict[str, Any],
    workspace_root: Optional[str] = None
) -> None:
    """
    Appends an action to the policy_pr_review_decisions.jsonl file.
    """
    d = _resolve_policy_autopilot_dir(workspace_root)
    d.mkdir(parents=True, exist_ok=True)
    log_path = d / "policy_pr_review_decisions.jsonl"
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proposal_id": proposal_id,
        "action": action,
        "operator_id": operator_id,
        "details": details
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_policy_pr_review_logs(workspace_root: Optional[str] = None) -> list:
    """Loads all append-only review decisions logs."""
    d = _resolve_policy_autopilot_dir(workspace_root)
    log_path = d / "policy_pr_review_decisions.jsonl"
    if not log_path.exists():
        return []
    logs = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                logs.append(json.loads(line))
    return logs
