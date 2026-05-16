import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIGuardrailTuningProposal, UIRedTeamFinding, UIAdversarialDriftEvent,
    UISecurityPostureFinding, GuardrailTuningStatus, GuardrailDomain,
    UIRepairSeverity
)
from services.observability.logging import get_logger

_log = get_logger("guardrail_tuner")

class GuardrailTunerAgent:
    """Phase 25: Analyzes security signals and generates guardrail tuning proposals."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_tuning_cycle(self) -> List[UIGuardrailTuningProposal]:
        """Orchestrates a full tuning cycle across all domains."""
        _log.info("Starting autonomous guardrail tuning cycle...")
        proposals = []
        
        # 1. Analyze Red Team Findings
        rt_proposals = await self._tune_from_red_team()
        proposals.extend(rt_proposals)
        
        # 2. Analyze Adversarial Drift
        drift_proposals = await self._tune_from_drift()
        proposals.extend(drift_proposals)
        
        # 3. Analyze Security Posture
        posture_proposals = await self._tune_from_posture()
        proposals.extend(posture_proposals)
        
        if proposals:
            await self.db.commit()
            _log.info(f"Generated {len(proposals)} new tuning proposals.")
        
        return proposals

    async def _tune_from_red_team(self) -> List[UIGuardrailTuningProposal]:
        """Generates proposals from critical/high Red Team findings."""
        stmt = select(UIRedTeamFinding).where(UIRedTeamFinding.severity.in_(["CRITICAL", "HIGH"]))
        result = await self.db.execute(stmt)
        findings = result.scalars().all()
        
        proposals = []
        for finding in findings:
            # Check if proposal already exists for this finding
            exists = await self._proposal_exists("RED_TEAM", finding.id)
            if exists:
                continue
                
            proposal = UIGuardrailTuningProposal(
                id=uuid.uuid4(),
                proposal_key=f"TP-RT-{finding.id.hex[:8].upper()}",
                source_type="RED_TEAM",
                source_id=finding.id,
                affected_guardrail=finding.affected_control or "GenericGuardrail",
                affected_policy_key=f"policy.{finding.affected_domain.lower() if finding.affected_domain else 'general'}.strictness",
                reason=f"Mitigation for Red Team Finding: {finding.description}",
                current_config_json={"threshold": 0.5}, # Mock current
                proposed_config_json={"threshold": 0.8 if finding.severity == "CRITICAL" else 0.7},
                expected_security_gain=0.3 if finding.severity == "CRITICAL" else 0.15,
                risk_level=finding.severity,
                status=GuardrailTuningStatus.DRAFT
            )
            self.db.add(proposal)
            proposals.append(proposal)
            
        return proposals

    async def _tune_from_drift(self) -> List[UIGuardrailTuningProposal]:
        """Generates proposals from adversarial drift events."""
        stmt = select(UIAdversarialDriftEvent).where(UIAdversarialDriftEvent.drift_score > 0.3)
        result = await self.db.execute(stmt)
        drifts = result.scalars().all()
        
        proposals = []
        for drift in drifts:
            exists = await self._proposal_exists("DRIFT", drift.id)
            if exists:
                continue
                
            proposal = UIGuardrailTuningProposal(
                id=uuid.uuid4(),
                proposal_key=f"TP-DR-{drift.id.hex[:8].upper()}",
                source_type="DRIFT",
                source_id=drift.id,
                affected_guardrail="DriftGuard",
                affected_policy_key=f"policy.{drift.domain.lower()}.drift_tolerance",
                reason=f"Counter-drift tuning for domain {drift.domain}. Detected score: {drift.drift_score}",
                current_config_json={"tolerance": 0.4},
                proposed_config_json={"tolerance": 0.2},
                expected_security_gain=0.2,
                risk_level="HIGH" if drift.drift_score > 0.5 else "MEDIUM",
                status=GuardrailTuningStatus.DRAFT
            )
            self.db.add(proposal)
            proposals.append(proposal)
            
        return proposals

    async def _tune_from_posture(self) -> List[UIGuardrailTuningProposal]:
        """Generates proposals from security posture gaps."""
        # This would link to Phase 23 findings
        return []

    async def _proposal_exists(self, source_type: str, source_id: uuid.UUID) -> bool:
        stmt = select(func.count()).select_from(UIGuardrailTuningProposal).where(
            UIGuardrailTuningProposal.source_type == source_type,
            UIGuardrailTuningProposal.source_id == source_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() > 0
