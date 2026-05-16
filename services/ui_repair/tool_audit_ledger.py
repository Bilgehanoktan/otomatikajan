import uuid
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIToolCallAudit

class ToolAuditLedger:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def record_call(
        self,
        tool_key: str,
        tenant_key: str,
        project_key: str,
        caller_id: str,
        action_type: str,
        input_data: Any,
        output_data: Any,
        policy_decision: str,
        risk_level: str,
        status: str = "SUCCESS",
        server_key: Optional[str] = None,
        redaction_applied: bool = False,
        cost_estimate: float = 0.0,
        latency_ms: int = 0,
        error_message: Optional[str] = None
    ) -> UIToolCallAudit:
        
        # Non-repudiable hashing of inputs and outputs
        input_str = json.dumps(input_data, sort_keys=True, default=str)
        output_str = json.dumps(output_data, sort_keys=True, default=str)
        
        input_hash = hashlib.sha256(input_str.encode()).hexdigest()
        output_hash = hashlib.sha256(output_str.encode()).hexdigest()
        
        audit = UIToolCallAudit(
            id=uuid.uuid4(),
            tool_key=tool_key,
            server_key=server_key,
            tenant_key=tenant_key,
            project_key=project_key,
            caller_type="AGENT", # Default for repair flows
            caller_id=caller_id,
            action_type=action_type,
            input_hash=input_hash,
            output_hash=output_hash,
            redaction_applied=redaction_applied,
            policy_decision=policy_decision,
            risk_level=risk_level,
            cost_estimate_usd=cost_estimate,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            evidence_hash=output_hash, # Link to SovereignEvidence
            created_at=datetime.now(timezone.utc)
        )
        
        self.db_session.add(audit)
        await self.db_session.commit()
        return audit
