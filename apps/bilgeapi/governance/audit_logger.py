import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from apps.bilgeapi.memory.db import get_workspace_db_session
from apps.bilgeapi.memory.repositories import AuditLogRepository

logger = logging.getLogger("bilgeapi.governance.audit")

def redact_sensitive_data(data: Any) -> Any:
    """Recursively searches for key names matching credentials/keys/tokens and redacts them."""
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            k_lower = k.lower()
            if any(term in k_lower for term in ["key", "secret", "token", "password", "auth"]):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = redact_sensitive_data(v)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    return data

class WorkspaceAuditLogger:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.jsonl_dir = workspace_dir / "audit"
        self.jsonl_path = self.jsonl_dir / "audit.jsonl"

    async def log_action(
        self,
        event_type: str,
        actor_id: str,
        actor_type: str,
        action: str,
        target: str,
        status: str,  # ALLOWED, DENIED, APPROVAL_REQUIRED
        risk_level: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        # Redact before persisting
        redacted_before = redact_sensitive_data(before_state) if before_state else None
        redacted_after = redact_sensitive_data(after_state) if after_state else None
        
        audit_record = None
        # 1. Store to SQLite DB
        try:
            async with get_workspace_db_session(self.workspace_dir) as session:
                repo = AuditLogRepository(session)
                audit_record = await repo.log_audit(
                    event_type=event_type,
                    actor_id=actor_id,
                    actor_type=actor_type,
                    action=action,
                    target=target,
                    status=status,
                    risk_level=risk_level,
                    before_state=redacted_before,
                    after_state=redacted_after
                )
        except Exception as e:
            logger.error(f"Failed to persist audit event to SQLite repository: {e}")

        # 2. Store to JSONL file
        try:
            self.jsonl_dir.mkdir(parents=True, exist_ok=True)
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "actor_id": actor_id,
                "actor_type": actor_type,
                "action": action,
                "target": target,
                "status": status,
                "risk_level": risk_level,
                "before_state": redacted_before,
                "after_state": redacted_after
            }
            if audit_record:
                log_entry["id"] = audit_record["id"]

            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write local JSONL audit log: {e}")

        return audit_record
