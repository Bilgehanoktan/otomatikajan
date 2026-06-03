from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Dict
from services.project_factory.artifacts import _resolve_project_dir

def record_implementation_event(
    project_id: str,
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    workspace_root: Optional[str] = None
) -> None:
    """
    Appends an event to implementation_events.jsonl inside the project folder.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)
    
    events_path = project_dir / "implementation_events.jsonl"
    
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "event_type": event_type,
        "message": message,
        "details": details or {}
    }
    
    with open(events_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def get_implementation_events(
    project_id: str,
    workspace_root: Optional[str] = None
) -> list[Dict[str, Any]]:
    """
    Retrieves all implementation events recorded for the project.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    events_path = project_dir / "implementation_events.jsonl"
    if not events_path.exists():
        return []
        
    events = []
    with open(events_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    return events
