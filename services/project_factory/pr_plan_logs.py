from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from services.project_factory.artifacts import _resolve_project_dir


def log_draft_pr_plan(
    project_id: str,
    action: str,
    operator_id: str,
    rationale: str,
    status: str,
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "event_id": f"PRPLAN-{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "action": action,
        "operator_id": operator_id,
        "rationale": rationale,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_operations_performed": False,
    }
    with open(project_dir / "draft_pr_decisions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def load_draft_pr_plan_logs(project_id: str, workspace_root: Optional[str] = None) -> List[Dict[str, Any]]:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    path = project_dir / "draft_pr_decisions.jsonl"
    if not path.exists():
        return []
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events
