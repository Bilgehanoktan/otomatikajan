import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

def _resolve_project_factory_root(workspace_root: Optional[str] = None) -> Path:
    if not workspace_root:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    workspace_path = Path(workspace_root).resolve()
    return (workspace_path / "project_outputs" / "project_factory").resolve()

def log_rebuild_action(
    operator_id: str,
    rationale: str,
    total_projects: int,
    release_archive_count: int,
    workspace_root: Optional[str] = None
) -> None:
    root = _resolve_project_factory_root(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    
    log_path = root / "archive_index_logs.jsonl"
    
    log_entry = {
        "event_id": f"AIDX-{uuid.uuid4().hex[:8].upper()}",
        "action": "REBUILD_ARCHIVE_INDEX",
        "operator_id": operator_id,
        "rationale": rationale,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_projects": total_projects,
        "release_archive_count": release_archive_count
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
