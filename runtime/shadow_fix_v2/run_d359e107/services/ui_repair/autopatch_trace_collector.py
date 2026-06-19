import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIAutoPatchTrace
from services.ui_repair.war_room_evidence_writer import WarRoomEvidenceWriter

class AutoPatchTraceCollector:
    """
    Phase 28: Collects and records observability traces for Auto-Patch executions.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence = WarRoomEvidenceWriter(db)

    async def start_trace(self, execution_id: uuid.UUID, step_name: str, agent_name: Optional[str] = None) -> UIAutoPatchTrace:
        trace = UIAutoPatchTrace(
            execution_id=execution_id,
            step_name=step_name,
            status="RUNNING",
            agent_name=agent_name,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(trace)
        await self.db.commit()
        await self.db.refresh(trace)
        return trace

    async def finish_trace(self, trace_id: uuid.UUID, status: str, 
                           cost_usd: float = 0.0, token_input: int = 0, token_output: int = 0,
                           error_message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        from sqlalchemy import select
        result = await self.db.execute(select(UIAutoPatchTrace).where(UIAutoPatchTrace.id == trace_id))
        trace = result.scalars().first()
        if not trace:
            return

        trace.status = status
        trace.finished_at = datetime.now(timezone.utc)
        
        # Handle potential naive/aware mismatch from SQLite
        start = trace.started_at
        end = trace.finished_at
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
            
        trace.duration_ms = int((end - start).total_seconds() * 1000)
        trace.cost_usd = cost_usd
        trace.token_input = token_input
        trace.token_output = token_output
        trace.error_message = error_message
        trace.metadata_json = metadata or {}
        
        # Write evidence for the step
        evidence_hash = self.evidence.write_execution_event(
            trace.execution_id, 
            f"trace_{trace.step_name}", 
            f"Step {trace.step_name} {status} in {trace.duration_ms}ms"
        )
        trace.evidence_hash = evidence_hash
        
        await self.db.commit()
