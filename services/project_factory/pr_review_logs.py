"""
PR Review Logs — append-only operator action log.

Records every review gate action: RUN, DECISION, etc.
Stored in pr_review_decisions.jsonl
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from services.project_factory.artifacts import _resolve_project_dir


def record_pr_review_decision(
    project_id: str,
    action: str,
    operator_id: str,
    rationale: str,
    details: Optional[Dict[str, Any]] = None,
    workspace_root: Optional[str] = None,
) -> None:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)
    log_file = project_dir / "pr_review_decisions.jsonl"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "operator_id": operator_id,
        "rationale": rationale,
        "details": details or {},
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_pr_review_decisions(
    project_id: str,
    workspace_root: Optional[str] = None,
) -> List[Dict[str, Any]]:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    log_file = project_dir / "pr_review_decisions.jsonl"
    if not log_file.exists():
        return []

    records = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
