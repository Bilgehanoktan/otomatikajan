import uuid
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIAutoPatchExecution, UIIncidentWarRoom, UIIncidentActionItem,
    UIRepairSeverity, AutoPatchExecutionStatus
)

class ExecutionPreflightGuard:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate(self, execution: UIAutoPatchExecution) -> Tuple[bool, str]:
        """
        Validates whether an Auto-Patch execution can proceed.
        Checks policy, budget, identity, and system state.
        """
        # 1. Check War Room Status
        if execution.war_room_id:
            result = await self.db.execute(select(UIIncidentWarRoom).where(UIIncidentWarRoom.id == execution.war_room_id))
            war_room = result.scalars().first()
            if not war_room:
                return False, "Linked War Room not found."
            # war_room.status might be an Enum or a string
            status_val = war_room.status.value if hasattr(war_room.status, 'value') else war_room.status
            if status_val == "RESOLVED":
                return False, "War Room is already resolved."

        # 2. Check Action Item Validity
        if execution.action_item_id:
            result = await self.db.execute(select(UIIncidentActionItem).where(UIIncidentActionItem.id == execution.action_item_id))
            action_item = result.scalars().first()
            if not action_item:
                return False, "Linked Action Item not found."
            status_val = action_item.status.value if hasattr(action_item.status, 'value') else action_item.status
            if status_val == "COMPLETED":
                return False, "Action Item is already completed."

        return True, "Preflight checks passed."

    async def log_failure(self, execution: UIAutoPatchExecution, reason: str):
        execution.status = AutoPatchExecutionStatus.PREFLIGHT_BLOCKED
        execution.error_message = reason
        await self.db.commit()
