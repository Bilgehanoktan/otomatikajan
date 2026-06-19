import json
import os
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from services.project_factory.artifacts import _resolve_policy_autopilot_dir

def append_policy_final_decision_log(entry: dict, workspace_root: Optional[str] = None):
    """Appends a new decision log to the final decision ledger."""
    d = _resolve_policy_autopilot_dir(workspace_root)
    d.mkdir(parents=True, exist_ok=True)
    
    log_path = d / "policy_final_decision_logs.jsonl"
    
    if "created_at" not in entry:
        entry["created_at"] = datetime.now(timezone.utc).isoformat()
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_policy_final_decision_logs(workspace_root: Optional[str] = None) -> list:
    """Loads all append-only final decision logs."""
    d = _resolve_policy_autopilot_dir(workspace_root)
    log_path = d / "policy_final_decision_logs.jsonl"
    if not log_path.exists():
        return []
    logs = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                logs.append(json.loads(line))
    return logs
