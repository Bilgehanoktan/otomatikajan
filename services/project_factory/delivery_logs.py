from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from services.project_factory.artifacts import _resolve_project_dir

def record_delivery_decision(
    project_id: str,
    action: str,
    operator_id: str,
    rationale: str,
    details: Optional[Dict[str, Any]] = None,
    workspace_root: Optional[str] = None
) -> None:
    """
    Appends a new decision log entry to delivery_decisions.jsonl.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    log_path = project_dir / "delivery_decisions.jsonl"
    
    created_at = datetime.utcnow().isoformat() + "Z"
    
    entry = {
        "project_id": project_id,
        "action": action,
        "operator_id": operator_id,
        "rationale": rationale,
        "timestamp": created_at,
        "details": details or {}
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_delivery_decisions(
    project_id: str,
    workspace_root: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Loads all log entries from delivery_decisions.jsonl.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    log_path = project_dir / "delivery_decisions.jsonl"
    
    if not log_path.exists():
        return []
        
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                try:
                    entries.append(json.loads(line_str))
                except Exception:
                    pass
    return entries
