import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UIGuardrailTuningProposal, GuardrailTuningStatus, UIRepairSeverity
)
from .guardrail_tuner_agent import GuardrailTunerAgent
from .defensive_pattern_synthesizer import DefensivePatternSynthesizer
from .policy_regression_verifier import PolicyRegressionVerifier
from .guardrail_canary_runner import GuardrailCanaryRunner
from .defense_tuning_policy import DefenseTuningPolicy
from .defense_evidence_writer import DefenseEvidenceWriter
from services.observability.logging import get_logger

_log = get_logger("optimization_engine")

class GuardrailOptimizationEngine:
    """Phase 25: Orchestrates the autonomous defense optimization lifecycle."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tuner = GuardrailTunerAgent(db)
        self.synthesizer = DefensivePatternSynthesizer(db)
        self.regression = PolicyRegressionVerifier(db)
        self.canary = GuardrailCanaryRunner(db)
        self.policy = DefenseTuningPolicy()
        self.evidence = DefenseEvidenceWriter(db)

    async def run_optimization_cycle(self):
        """Main autonomous loop for finding-to-optimization flow."""
        _log.info("Starting autonomous defense optimization cycle...")
        
        # 1. Synthesize Patterns
        await self.synthesizer.synthesize_patterns()
        
        # 2. Generate Proposals
        proposals = await self.tuner.run_tuning_cycle()
        
        for p in proposals:
            await self.evidence.write_tuning_event("PROPOSAL_GENERATED", {
                "proposal_id": str(p.id),
                "key": p.proposal_key,
                "domain": p.affected_guardrail
            })
            
        return proposals

    async def promote_proposal(self, proposal_id: uuid.UUID):
        """Moves a proposal through the verification stages."""
        stmt = select(UIGuardrailTuningProposal).where(UIGuardrailTuningProposal.id == proposal_id)
        res = await self.db.execute(stmt)
        proposal = res.scalar_one_or_none()
        
        if not proposal:
            return None
            
        # Safety Check: Never weaken global policy
        if not self.policy.validate_improvement(proposal):
            proposal.status = GuardrailTuningStatus.REJECTED
            proposal.reason += "\n[SAFETY_BLOCK] Proposal attempted to weaken global security policy."
            await self.db.commit()
            return proposal

        # Phase transition based on current status
        if proposal.status == GuardrailTuningStatus.DRAFT:
            # 1. Run Regression
            await self.regression.run_regression(proposal_id)
            await self.evidence.write_tuning_event("REGRESSION_COMPLETED", {"proposal_id": str(proposal_id)})
            
        elif proposal.status == GuardrailTuningStatus.REGRESSION_PASSED:
            # 2. Run Canary
            await self.canary.start_canary(proposal_id)
            await self.evidence.write_tuning_event("CANARY_STARTED", {"proposal_id": str(proposal_id)})
            
        elif proposal.status == GuardrailTuningStatus.CANARY_PASSED:
            # 3. Request Governance Approval
            proposal.status = GuardrailTuningStatus.GOVERNANCE_REQUESTED
            await self.evidence.write_tuning_event("GOVERNANCE_REQUESTED", {"proposal_id": str(proposal_id)})
            
        await self.db.commit()
        return proposal

    async def apply_proposal(self, proposal_id: uuid.UUID):
        """Final application of a proposal after governance approval."""
        stmt = select(UIGuardrailTuningProposal).where(UIGuardrailTuningProposal.id == proposal_id)
        res = await self.db.execute(stmt)
        proposal = res.scalar_one_or_none()
        
        if not proposal or proposal.status != GuardrailTuningStatus.APPROVED:
            raise ValueError("Only APPROVED proposals can be applied.")
            
        _log.info(f"Applying tuning proposal {proposal.proposal_key}...")
        
        # In Phase 25, we simulate the mutation to the policy engine
        # In production, this would call PolicyAsCodeEngine.update_config()
        
        proposal.status = GuardrailTuningStatus.APPLIED
        await self.evidence.write_tuning_event("PROPOSAL_APPLIED", {"proposal_id": str(proposal_id)})
        
        await self.db.commit()
        return proposal
