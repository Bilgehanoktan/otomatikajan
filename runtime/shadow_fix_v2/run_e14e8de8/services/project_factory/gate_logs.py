from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from services.project_factory.artifacts import _resolve_project_dir

def record_gate_decision(
    project_id: str,
    action: str,
    operator_id: str,
    rationale: str,
    details: Optional[Dict[str, Any]] = None,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Appends a new gate decision record to the append-only gate_decisions.jsonl log.
    Never updates existing entries.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)

    decision_id = f"DEC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    created_at = datetime.now(timezone.utc).isoformat() + "Z"

    log_entry = {
        "decision_id": decision_id,
        "project_id": project_id,
        "action": action,
        "operator_id": operator_id,
        "rationale": rationale,
        "created_at": created_at,
        "details": details or {}
    }

    log_file = project_dir / "gate_decisions.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return log_entry

def get_gate_decisions(
    project_id: str,
    workspace_root: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Loads all gate decision log entries for a given project from gate_decisions.jsonl.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    log_file = project_dir / "gate_decisions.jsonl"

    if not log_file.exists():
        return []

    decisions = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    decisions.append(json.loads(line))
                except Exception:
                    pass
    return decisions
