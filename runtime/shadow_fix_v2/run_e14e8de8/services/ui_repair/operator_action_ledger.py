import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIOperatorActionLedger

class OperatorActionLedger:
    """Records every operator action with mandatory rationale."""
    
    @staticmethod
    async def record_action(
        db: AsyncSession, 
        rollout_id: str, 
        operator: str, 
        action_type: str, 
        rationale: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        before_state: Optional[Dict[Any, Any]] = None,
        after_state: Optional[Dict[Any, Any]] = None
    ):
        if not rationale or len(rationale) < 10:
            raise ValueError("Rationale is mandatory and must be descriptive (min 10 chars).")
            
        entry = UIOperatorActionLedger(
            id=str(uuid.uuid4()),
            rollout_id=rollout_id,
            operator=operator,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            rationale=rationale,
            before_state_json=before_state or {},
            after_state_json=after_state or {},
            created_at=datetime.now(timezone.utc)
        )
        db.add(entry)
        await db.commit()
        return entry

    @staticmethod
    async def get_ledger(db: AsyncSession, rollout_id: str):
        stmt = select(UIOperatorActionLedger).where(UIOperatorActionLedger.rollout_id == rollout_id).order_by(UIOperatorActionLedger.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
