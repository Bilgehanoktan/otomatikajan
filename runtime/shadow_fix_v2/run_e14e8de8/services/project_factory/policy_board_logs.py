import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

def log_policy_board_decision(
    proposal_id: str,
    action: str,
    from_status: str,
    to_status: str,
    operator_id: str,
    rationale: str,
    risk_acknowledgement: bool,
    workspace_root: Optional[str] = None
) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    log_file = d / "policy_board_decisions.jsonl"
    
    event = {
        "decision_id": f"PBD-{datetime.now(timezone.utc).timestamp()}",
        "proposal_id": proposal_id,
        "action": action,
        "from_status": from_status,
        "to_status": to_status,
        "operator_id": operator_id,
        "rationale": rationale,
        "risk_acknowledgement": risk_acknowledgement,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
