import uuid
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIGuardrailCanaryRun, UIGuardrailTuningProposal, GuardrailTuningStatus
)
from services.observability.logging import get_logger

_log = get_logger("canary_runner")

class GuardrailCanaryRunner:
    """Phase 25: Executes tuning proposals in shadow/canary mode to observe real-world impact."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_canary(self, proposal_id: uuid.UUID, scope: Optional[Dict[str, Any]] = None) -> UIGuardrailCanaryRun:
        """Starts a canary run for a proposal."""
        proposal_stmt = select(UIGuardrailTuningProposal).where(UIGuardrailTuningProposal.id == proposal_id)
        proposal_res = await self.db.execute(proposal_stmt)
        proposal = proposal_res.scalar_one_or_none()
        
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found.")
            
        _log.info(f"Starting canary validation for proposal {proposal.proposal_key}...")
        
        run = UIGuardrailCanaryRun(
            id=uuid.uuid4(),
            proposal_id=proposal_id,
            status="RUNNING",
            canary_scope_json=scope or {"tenant": "CANARY_POOL_01", "traffic_share": 0.1},
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        
        proposal.status = GuardrailTuningStatus.CANARY_RUNNING
        await self.db.commit()
        
        return run

    async def complete_canary(self, run_id: uuid.UUID, force_success: bool = False) -> UIGuardrailCanaryRun:
        """Simulates completion of a canary run and evaluates metrics."""
        stmt = select(UIGuardrailCanaryRun).where(UIGuardrailCanaryRun.id == run_id)
        result = await self.db.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            raise ValueError(f"Canary run {run_id} not found.")
            
        _log.info(f"Finalizing canary run {run_id}...")
        
        # 1. Simulate data collection
        # In production, this would read from real-time telemetry
        observed = random.randint(100, 500)
        blocked = random.randint(10, 50)
        unexpected_allows = 0 if force_success else random.randint(0, 5)
        unexpected_blocks = 0 if force_success else random.randint(0, 10)
        
        run.observed_events = observed
        run.blocked_events = blocked
        run.unexpected_allows = unexpected_allows
        run.unexpected_blocks = unexpected_blocks
        
        # 2. Evaluate Success
        if force_success:
            run.status = "PASSED"
            run.rollback_required = False
        elif unexpected_allows > 2 or unexpected_blocks > 5:
            run.status = "FAILED"
            run.rollback_required = True
        else:
            run.status = "PASSED"
            run.rollback_required = False
            
        run.finished_at = datetime.now(timezone.utc)
        run.result_summary_json = {
            "metrics": {
                "block_rate": f"{(blocked/observed)*100:.1f}%",
                "false_positive_rate": f"{(unexpected_blocks/observed)*100:.1f}%"
            }
        }
        
        # 3. Update Proposal
        proposal_stmt = select(UIGuardrailTuningProposal).where(UIGuardrailTuningProposal.id == run.proposal_id)
        proposal_res = await self.db.execute(proposal_stmt)
        proposal = proposal_res.scalar_one()
        
        proposal.status = GuardrailTuningStatus.CANARY_PASSED if run.status == "PASSED" else GuardrailTuningStatus.CANARY_FAILED
        
        await self.db.commit()
        _log.info(f"Canary run finished. Status: {run.status}")
        
        return run
