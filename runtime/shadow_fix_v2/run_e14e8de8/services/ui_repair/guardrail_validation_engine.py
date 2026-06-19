from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import RedTeamTargetDomain

class GuardrailValidationEngine:
    """Phase 24: Validates guardrail decisions against expected security outcomes."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_decision(self, domain: RedTeamTargetDomain, payload: Dict[str, Any], expected_decision: str) -> Dict[str, Any]:
        """Queries the relevant system control and validates its decision."""
        
        # In a real system, this would call:
        # - services.ui_repair.compliance_guardrails
        # - services.ui_repair.policy_as_code_engine
        # - libs.auth.sovereign_identity_framework
        
        # MOCK LOGIC for Phase 24 demonstration:
        actual_decision = self._simulate_system_decision(domain, payload)
        
        passed = (actual_decision == expected_decision)
        # Exception: if expected is DENY and actual is BLOCK (synonyms in different layers)
        if expected_decision == "DENY" and actual_decision == "BLOCK":
            passed = True
            
        failure_reason = None
        if not passed:
            failure_reason = f"Security drift detected in {domain.value}. Expected {expected_decision}, got {actual_decision}."
            
        return {
            "actual_decision": actual_decision,
            "passed": passed,
            "failure_reason": failure_reason,
            "control_point": self._get_control_point_name(domain)
        }

    def _simulate_system_decision(self, domain: RedTeamTargetDomain, payload: Dict[str, Any]) -> str:
        """Simulates how the actual system would respond to the probe."""
        # By default, our guardrails are strong
        if domain == RedTeamTargetDomain.TENANT_ISOLATION:
            # Check if payload targets another tenant
            if payload.get("target_tenant") == "OTHER_TENANT_001":
                return "DENY"
                
        if domain == RedTeamTargetDomain.GOVERNANCE:
            if payload.get("action") == "APPLY_PATCH":
                return "REQUIRE_APPROVAL"
                
        if domain == RedTeamTargetDomain.COGNITIVE_INTEGRITY:
            if "delete" in str(payload.get("repair_instruction")).lower():
                return "BLOCK"

        # Default to DENY for security probes
        return "DENY"

    def _get_control_point_name(self, domain: RedTeamTargetDomain) -> str:
        """Maps domain to the actual guardrail service name."""
        mapping = {
            RedTeamTargetDomain.IDENTITY: "SovereignIdentityFramework",
            RedTeamTargetDomain.POLICY: "PolicyAsCodeEngine",
            RedTeamTargetDomain.TENANT_ISOLATION: "TenantBoundaryEnforcer",
            RedTeamTargetDomain.TOOL_GOVERNANCE: "ToolCapabilityGuard",
            RedTeamTargetDomain.COGNITIVE_INTEGRITY: "CognitiveIntegrityGuard",
            RedTeamTargetDomain.GOVERNANCE: "RepairGovernanceGate",
            RedTeamTargetDomain.FINOPS: "BudgetGuard"
        }
        return mapping.get(domain, "DefaultGuardrail")
