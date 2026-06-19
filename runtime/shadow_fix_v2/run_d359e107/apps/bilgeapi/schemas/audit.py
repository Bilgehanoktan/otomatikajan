from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class AuditEvent(BaseModel):
    id: str
    event_type: str
    actor_id: str
    actor_type: str
    entity_type: str
    entity_id: str
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
