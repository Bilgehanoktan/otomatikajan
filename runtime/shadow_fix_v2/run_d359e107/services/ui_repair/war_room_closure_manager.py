import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIAutoPatchExecution, UIIncidentActionItem, UIIncidentWarRoom,
    WarRoomStatus, AutoPatchExecutionStatus
)

class WarRoomClosureManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def close_action_item(self, execution: UIAutoPatchExecution) -> bool:
        """
        Closes the linked action item after successful verification.
        """
        if not execution.action_item_id or execution.status != AutoPatchExecutionStatus.VERIFIED:
            return False

        result = await self.db.execute(select(UIIncidentActionItem).where(UIIncidentActionItem.id == execution.action_item_id))
        action_item = result.scalars().first()
        if action_item:
            action_item.status = "COMPLETED"
            await self.db.commit()
            return True
        return False

    async def recommend_war_room_resolution(self, war_room_id: uuid.UUID) -> Dict[str, Any]:
        """
        Checks if all critical action items are closed and recommends resolution.
        """
        result = await self.db.execute(select(UIIncidentWarRoom).where(UIIncidentWarRoom.id == war_room_id))
        war_room = result.scalars().first()
        if not war_room:
            return {"can_resolve": False, "reason": "War Room not found."}

        res_actions = await self.db.execute(
            select(UIIncidentActionItem).where(
                UIIncidentActionItem.war_room_id == war_room_id,
                UIIncidentActionItem.status != "COMPLETED"
            )
        )
        open_actions = res_actions.scalars().all()

        if not open_actions:
            return {
                "can_resolve": True,
                "recommendation": "All action items completed. Recommend resolving the War Room.",
                "rationale": "Autonomous remediation successfully verified for all critical paths."
            }
        
        return {
            "can_resolve": False,
            "open_actions_count": len(open_actions),
            "reason": f"There are still {len(open_actions)} open action items."
        }
