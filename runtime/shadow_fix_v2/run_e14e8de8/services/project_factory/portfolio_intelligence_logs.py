import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from services.project_factory.artifacts import _resolve_project_factory_root

def log_portfolio_intelligence_run(
    operator_id: str,
    rationale: str,
    portfolio_size: int,
    recommendation_count: int,
    workspace_root: Optional[str] = None
) -> None:
    root = _resolve_project_factory_root(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    
    log_file = root / "portfolio_intelligence_logs.jsonl"
    
    event = {
        "event_id": f"PINT-{datetime.now(timezone.utc).timestamp()}",
        "action": "RUN_PORTFOLIO_INTELLIGENCE",
        "operator_id": operator_id,
        "rationale": rationale,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "portfolio_size": portfolio_size,
        "recommendation_count": recommendation_count
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
