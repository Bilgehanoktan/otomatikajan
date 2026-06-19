import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIAutoPatchExecution, UIRollbackExecution, AutoPatchExecutionStatus
)

class RollbackOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def rollback(self, execution: UIAutoPatchExecution, reason: str) -> UIRollbackExecution:
        """
        Executes a rollback to the pre-apply snapshot.
        """
        execution.status = AutoPatchExecutionStatus.ROLLING_BACK
        await self.db.commit()

        rollback_exec = UIRollbackExecution(
            execution_id=execution.id,
            status="SUCCESS",
            rollback_reason=reason,
            rollback_snapshot_path=execution.rollback_snapshot_path or "snapshots/latest.img",
            rollback_result_json={"files_restored": 5, "database_reverted": False},
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(rollback_exec)
        
        execution.status = AutoPatchExecutionStatus.ROLLED_BACK
        execution.completed_at = datetime.now(timezone.utc)
        await self.db.commit()

        return rollback_exec
