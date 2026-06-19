import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UICognitiveIntegrityCheck,
    UICognitiveStatus,
    UICognitiveDecision,
    UICognitiveOutputType,
    UILLMClaim,
    UIHallucinationFinding,
    UISemanticDriftEvent,
    UIPolicyDrift,
    UIRepairCase,
    UICognitiveFindingType
)
from sqlalchemy import select
from libs.infra.ws_manager import ws_manager
from services.ui_repair.hallucination_firewall import HallucinationFirewall
from services.ui_repair.semantic_drift_detector import SemanticDriftDetector
from services.ui_repair.claim_verification_engine import ClaimVerificationEngine
from services.ui_repair.repair_instruction_validator import RepairInstructionValidator

logger = logging.getLogger(__name__)

class CognitiveIntegrityGuard:
    """Phase 20: Main orchestrator for zero-trust cognitive verification."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.hallucination_firewall = HallucinationFirewall(db)
        self.drift_detector = SemanticDriftDetector(db)
        self.claim_engine = ClaimVerificationEngine(db)
        self.instruction_validator = RepairInstructionValidator(db)

    async def run_check(self, 
                  source_type: str, 
                  source_id: str, 
                  agent_name: str, 
                  output_type: UICognitiveOutputType, 
                  content: str, 
                  expected_context: Optional[Dict[str, Any]] = None) -> UICognitiveIntegrityCheck:
        
        # 1. Initialize Check Record
        check = UICognitiveIntegrityCheck(
            source_type=source_type,
            source_id=source_id,
            agent_name=agent_name,
            output_type=output_type,
            status=UICognitiveStatus.PENDING
        )
        self.db.add(check)
        await self.db.commit()
        await self.db.refresh(check)
        
        check_id = str(check.id)
        
        # 2. Run Hallucination Firewall
        findings = await self.hallucination_firewall.check_hallucinations(check_id, content, source_id)
        for f in findings:
            self.db.add(f)
            
        # 3. Run Semantic Drift Detection
        if expected_context:
            drift_event = await self.drift_detector.detect_drift(check_id, content, expected_context, source_id, source_type)
            if drift_event:
                self.db.add(drift_event)
                check.semantic_drift_score = drift_event.drift_score
        
        # 3.5 Check for Active Policy Drifts (Phase 20 Federated Integration)
        policy_drifts = await self._check_policy_drifts(source_id, source_type)
        for pd in policy_drifts:
            # Wrap as a finding for score calculation
            finding = UIHallucinationFinding(
                check_id=check_id,
                finding_type=UICognitiveFindingType.POLICY_DRIFT,
                severity=pd.drift_level,
                description=f"Active policy drift detected: {pd.drift_type} on {pd.policy_key}",
                source_context={"policy_key": pd.policy_key, "drift_type": pd.drift_type}
            )
            self.db.add(finding)
            findings.append(finding)
        
        # 4. Run Claim Verification
        claims = await self.claim_engine.verify_claims(check_id, content, source_id)
        for c in claims:
            self.db.add(c)
            
        # 5. Run Repair Instruction Validation (if applicable)
        if output_type == UICognitiveOutputType.OPENSWE_REPAIR_INSTRUCTION:
            safety_findings = await self.instruction_validator.validate_instructions(check_id, content)
            for sf in safety_findings:
                self.db.add(sf)
                findings.append(sf)

        # 6. Calculate Scores
        self._calculate_scores(check, findings, claims)
        
        # 7. Make Final Decision
        self._make_decision(check, findings, claims)
        
        await self.db.commit()

        # 8. Broadcast WebSocket Notification (Phase 20)
        await ws_manager.broadcast_event(
            event_type="COGNITIVE_INTEGRITY_CHECK_COMPLETED",
            component=agent_name,
            rationale=f"Cognitive integrity check for {output_type} completed with decision: {check.decision}",
            severity="info" if check.decision == UICognitiveDecision.ALLOW else "critical",
            category="governance",
            summary=f"Integrity Guard: {check.decision} (Hallucination: {check.hallucination_score:.2f}, Grounding: {check.evidence_grounding_score:.2f})"
        )

        return check

    async def _check_policy_drifts(self, source_id: str, source_type: str) -> List[UIPolicyDrift]:
        """Queries for active policy drifts relevant to the repair context."""
        try:
            # We need to find the case to get the tenant/cluster/project keys
            if source_type == "REPAIR_CASE":
                q = select(UIRepairCase).where(UIRepairCase.id == source_id)
                res = await self.db.execute(q)
                case = res.scalar_one_or_none()
                if case:
                    dq = select(UIPolicyDrift).where(
                        UIPolicyDrift.tenant_key == case.tenant_key,
                        UIPolicyDrift.status == "DETECTED"
                    )
                    dres = await self.db.execute(dq)
                    return list(dres.scalars().all())
            return []
        except Exception as e:
            logger.warning(f"Failed to check policy drifts: {e}")
            return []

    def _calculate_scores(self, check: UICognitiveIntegrityCheck, findings: List[UIHallucinationFinding], claims: List[UILLMClaim]):
        # Hallucination Score (1.0 - penalty for each finding)
        hallucination_penalty = sum(0.2 for f in findings if f.severity != "LOW")
        # Add extra penalty for Policy Drifts
        policy_penalty = sum(0.3 for f in findings if f.finding_type == UICognitiveFindingType.POLICY_DRIFT and f.severity in ["HIGH", "CRITICAL"])
        
        check.hallucination_score = max(0.0, 1.0 - hallucination_penalty - policy_penalty)
        
        # Claim Verification Score
        if claims:
            verified_count = sum(1 for c in claims if c.verification_status == "VERIFIED")
            contradicted_count = sum(1 for c in claims if c.verification_status == "CONTRADICTED")
            check.claim_verification_score = (verified_count - (contradicted_count * 2)) / len(claims)
            check.claim_verification_score = max(0.0, min(1.0, check.claim_verification_score))
        else:
            check.claim_verification_score = 0.5 # Neutral if no claims found
            
        # Grounding Score (Simplified for demo)
        check.evidence_grounding_score = 0.8 if check.reason and ("evidence" in check.reason or "log" in check.reason) else 0.5
        
        # Aggregate Integrity Score
        check.integrity_score = (
            check.hallucination_score * 0.4 +
            check.claim_verification_score * 0.3 +
            (1.0 - check.semantic_drift_score) * 0.3
        )

    def _make_decision(self, check: UICognitiveIntegrityCheck, findings: List[UIHallucinationFinding], claims: List[UILLMClaim]):
        critical_hallucination = any(f.severity in ["HIGH", "CRITICAL"] for f in findings)
        
        if critical_hallucination or check.integrity_score < 0.5:
            check.decision = UICognitiveDecision.BLOCK_ACTION
            check.status = UICognitiveStatus.BLOCKED
            check.reason = "Critical hallucinations or extremely low integrity score detected."
        elif check.integrity_score < 0.7:
            check.decision = UICognitiveDecision.REQUIRE_MANUAL_REVIEW
            check.status = UICognitiveStatus.MANUAL_REVIEW_REQUIRED
            check.reason = "Integrity score marginal. Manual verification required."
        elif check.integrity_score < 0.85:
            check.decision = UICognitiveDecision.ALLOW_WITH_WARNING
            check.status = UICognitiveStatus.WARNING
            check.reason = "Minor issues detected, but overall grounded."
        else:
            check.decision = UICognitiveDecision.ALLOW
            check.status = UICognitiveStatus.PASSED
            check.reason = "Cognitive integrity verified."
