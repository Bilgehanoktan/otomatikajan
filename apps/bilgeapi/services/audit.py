import os
import json
import logging
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional
from apps.bilgeapi.schemas.audit import AuditEvent
from apps.bilgeapi.repositories.interface import AuditRepository

logger = logging.getLogger("bilgeapi.audit")

def redact_sensitive_data(data: Any) -> Any:
    """Recursively search for key names matching credentials/keys/tokens and redact them."""
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

class AuditService:
    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    async def log_event(
        self,
        event_type: str,
        actor_id: str,
        actor_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str = "default",
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        now = datetime.now(timezone.utc)
        event = AuditEvent(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id,
            correlation_id=correlation_id,
            ip_address=ip_address,
            user_agent=user_agent,
            before_state=redact_sensitive_data(before_state) if before_state else None,
            after_state=redact_sensitive_data(after_state) if after_state else None,
            metadata=redact_sensitive_data(metadata or {}),
            created_at=now
        )
        object.__setattr__(event, 'tenant_id', tenant_id)
        
        # Repository write is best-effort. Audit persistence degradation must not
        # turn request auth / business flows into 500s.
        try:
            await self.audit_repo.write(event, tenant_id)
        except Exception as e:
            logger.error(f"Failed to persist audit event to repository: {e}")
        
        # Write to local JSONL log file
        try:
            log_dir = "apps/bilgeapi"
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "audit.log")
            
            # Serialize event and append to file using pydantic's built-in serialization
            event_json = event.model_dump_json()
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(event_json + "\n")
        except Exception as e:
            # Safe catch-all to prevent failing main API execution
            logger.error(f"Failed to write local audit log file: {e}")
            
        return event
