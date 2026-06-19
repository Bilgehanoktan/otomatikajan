import uuid
import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from libs.db.models.ui_repair_models import (
    UIAutoPatchExecution, AutoPatchExecutionStatus
)
from services.ui_repair.autopatch_v2_orchestrator import AutoPatchV2Orchestrator

class RemediationExecutionEngine:
    """
    High-level engine to drive the Auto-Patch v2 pipeline steps.
    """
    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = AutoPatchV2Orchestrator(db)

    async def run_full_cycle(self, execution_id: uuid.UUID) -> Dict[str, Any]:
        """
        Drives the execution from start to verification (Governance Gate).
        Apply is kept manual/operator-triggered.
        """
        # 1. Preflight
        preflight = await self.orchestrator.run_preflight(execution_id)
        if preflight["status"] != "success":
            return preflight

        # 2. Planning & Generation
        gen = await self.orchestrator.plan_and_generate(execution_id)
        if gen["status"] != "success":
            return gen

        # 3. Verification
        execution = self.db.query(UIAutoPatchExecution).filter(UIAutoPatchExecution.id == execution_id).first()
        if not execution:
            return {"status": "error", "message": "Execution lost during planning."}
            
        run = self.orchestrator.verifier.run_verification(execution)
        
        return {
            "status": "success",
            "execution_id": str(execution_id),
            "verification_status": run.status,
            "next_step": "GOVERNANCE_APPROVAL_REQUIRED"
        }
