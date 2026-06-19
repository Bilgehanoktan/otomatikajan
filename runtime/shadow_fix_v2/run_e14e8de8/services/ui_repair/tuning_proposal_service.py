import uuid
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIGuardrailTuningProposal, GuardrailTuningStatus, UIDefensivePattern,
    UIPolicyRegressionRun, UIGuardrailCanaryRun
)

class TuningProposalService:
    """Phase 25: Management service for guardrail tuning proposals."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_proposals(self) -> List[UIGuardrailTuningProposal]:
        stmt = select(UIGuardrailTuningProposal).order_by(desc(UIGuardrailTuningProposal.created_at))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_proposal(self, proposal_id: uuid.UUID) -> Optional[UIGuardrailTuningProposal]:
        stmt = select(UIGuardrailTuningProposal).where(UIGuardrailTuningProposal.id == proposal_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def approve_proposal(self, proposal_id: uuid.UUID) -> Optional[UIGuardrailTuningProposal]:
        proposal = await self.get_proposal(proposal_id)
        if proposal and proposal.status == GuardrailTuningStatus.GOVERNANCE_REQUESTED:
            proposal.status = GuardrailTuningStatus.APPROVED
            await self.db.commit()
        return proposal

    async def reject_proposal(self, proposal_id: uuid.UUID, reason: str) -> Optional[UIGuardrailTuningProposal]:
        proposal = await self.get_proposal(proposal_id)
        if proposal:
            proposal.status = GuardrailTuningStatus.REJECTED
            proposal.reason += f"\n[REJECTION] {reason}"
            await self.db.commit()
        return proposal

    async def get_patterns(self) -> List[UIDefensivePattern]:
        stmt = select(UIDefensivePattern).order_by(desc(UIDefensivePattern.created_at))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_regression_runs(self, proposal_id: Optional[uuid.UUID] = None) -> List[UIPolicyRegressionRun]:
        stmt = select(UIPolicyRegressionRun)
        if proposal_id:
            stmt = stmt.where(UIPolicyRegressionRun.proposal_id == proposal_id)
        stmt = stmt.order_by(desc(UIPolicyRegressionRun.created_at))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_canary_runs(self, proposal_id: Optional[uuid.UUID] = None) -> List[UIGuardrailCanaryRun]:
        stmt = select(UIGuardrailCanaryRun)
        if proposal_id:
            stmt = stmt.where(UIGuardrailCanaryRun.proposal_id == proposal_id)
        stmt = stmt.order_by(desc(UIGuardrailCanaryRun.created_at))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
