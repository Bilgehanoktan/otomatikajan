import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UISecurityPostureFinding, 
    UISecurityRemediationPlan,
    RemediationStatus,
    RemediationType,
    UIRepairSeverity
)
from services.ui_repair.security_finding_classifier import SecurityFindingClassifier

logger = logging.getLogger(__name__)

class RemediationPlanner:
    """Phase 22: Generates remediation plans for security findings."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.classifier = SecurityFindingClassifier(db)

    async def generate_plan(self, finding: UISecurityPostureFinding) -> UISecurityRemediationPlan:
        """Creates a remediation plan for a given finding."""
        classification = await self.classifier.classify_finding(finding)
        
        severity = classification["severity"]
        risk_level = classification["risk_level"]
        
        remediation_type = self._determine_remediation_type(finding, severity)
        recommended_action = self._generate_recommended_action(finding, remediation_type)
        
        # Guardrails logic
        requires_approval = True
        requires_patch = False
        requires_operator = True
        
        if severity == UIRepairSeverity.LOW.value:
            requires_operator = False # Can be auto-fix proposed
            requires_patch = True if "patch" in recommended_action.lower() else False
        elif severity == UIRepairSeverity.CRITICAL.value:
            requires_approval = True
            requires_operator = True
            # Critical findings should NOT have auto-fix enabled in the policy engine
            
        plan = UISecurityRemediationPlan(
            id=uuid.uuid4(),
            finding_id=finding.id,
            finding_type=finding.control_key,
            severity=severity,
            risk_level=risk_level,
            remediation_type=remediation_type,
            recommended_action=recommended_action,
            affected_module=None, # To be refined by agent later
            affected_policy=None,
            affected_route=None,
            requires_approval=requires_approval,
            requires_patch=requires_patch,
            requires_operator=requires_operator,
            status=RemediationStatus.PLANNED
        )
        
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        
        return plan

    def _determine_remediation_type(self, finding: UISecurityPostureFinding, severity: str) -> RemediationType:
        ck = finding.control_key.lower()
        if "policy" in ck or "drift" in ck:
            return RemediationType.POLICY_TIGHTENING
        if "trust" in ck or "identity" in ck:
            return RemediationType.IDENTITY_TRUST_REPAIR
        if "evidence" in ck or "hash" in ck:
            return RemediationType.EVIDENCE_CHAIN_REPAIR
        if "tenant" in ck or "isolation" in ck:
            return RemediationType.TENANT_ISOLATION_REPAIR
        if "mcp" in ck or "tool" in ck:
            return RemediationType.TOOL_GOVERNANCE_REPAIR
        if "metadata" in ck:
            return RemediationType.COMPLIANCE_METADATA_FIX
            
        if severity == UIRepairSeverity.CRITICAL.value:
            return RemediationType.MANUAL_SECURITY_REVIEW
            
        return RemediationType.CONFIG_HARDENING

    def _generate_recommended_action(self, finding: UISecurityPostureFinding, r_type: RemediationType) -> str:
        if r_type == RemediationType.POLICY_TIGHTENING:
            return f"Re-align local policy for {finding.control_key} with global standard. Tighten relaxation parameters."
        if r_type == RemediationType.IDENTITY_TRUST_REPAIR:
            return f"Initiate trust-score recalibration for identity associated with {finding.control_key}."
        if r_type == RemediationType.EVIDENCE_CHAIN_REPAIR:
            return f"Re-generate missing evidence hashes and verify block-integrity for {finding.control_key}."
        if r_type == RemediationType.MANUAL_SECURITY_REVIEW:
            return f"CRITICAL finding detected in {finding.control_key}. STOP autonomous operations and initiate manual forensic review."
            
        return f"Perform automated configuration hardening for {finding.control_key}."
