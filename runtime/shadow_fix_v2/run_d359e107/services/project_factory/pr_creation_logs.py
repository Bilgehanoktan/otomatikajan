import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from services.project_factory.artifacts import _resolve_project_dir

def record_pr_creation_decision(
    project_id: str,
    action: str,
    operator_id: str,
    rationale: str,
    details: Optional[Dict[str, Any]] = None,
    workspace_root: Optional[str] = None
) -> None:
    """
    Appends a new decision record to the draft_pr_creation_logs.jsonl file.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = project_dir / "draft_pr_creation_logs.jsonl"
    
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "operator_id": operator_id,
        "rationale": rationale,
        "details": details or {}
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def get_pr_creation_logs(
    project_id: str,
    workspace_root: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves all records from the draft_pr_creation_logs.jsonl file.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    log_file = project_dir / "draft_pr_creation_logs.jsonl"
    
    if not log_file.exists():
        return []
        
    records = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
                
    return records
