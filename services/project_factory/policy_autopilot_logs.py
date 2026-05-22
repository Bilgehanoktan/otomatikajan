import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

def log_policy_autopilot_event(
    action: str,
    operator_id: str,
    rationale: str,
    details: Dict[str, Any],
    workspace_root: Optional[str] = None
) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    log_file = d / "policy_autopilot_logs.jsonl"
    
    event = {
        "event_id": f"POL-AUTO-{datetime.now(timezone.utc).timestamp()}",
        "action": action,
        "operator_id": operator_id,
        "rationale": rationale,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
