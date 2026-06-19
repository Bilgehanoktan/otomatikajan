import logging
from typing import Dict, Any, Optional
from libs.db.models.ui_repair_models import UIRepairSeverity, UISecurityPostureFinding

logger = logging.getLogger(__name__)

class SecurityFindingClassifier:
    """Phase 22: Classifies security findings into risk levels and severities."""
    
    def __init__(self, db):
        self.db = db

    async def classify_finding(self, finding: UISecurityPostureFinding) -> Dict[str, Any]:
        """
        Determines the severity and risk level of a posture finding.
        Returns a dict with 'severity', 'risk_level', and 'finding_category'.
        """
        # Default mapping based on control_key keywords if not explicitly set
        control_key = finding.control_key.lower()
        rationale = finding.rationale.lower()
        
        # 1. CRITICAL
        if any(k in control_key or k in rationale for k in ["bypass", "secret", "cross-tenant", "replay", "legal-hold"]):
            return {
                "severity": UIRepairSeverity.CRITICAL.value,
                "risk_level": "CRITICAL",
                "finding_category": "GOVERNANCE_OR_DATA_SECURITY"
            }
            
        # 2. HIGH
        if any(k in control_key or k in rationale for k in ["evidence-chain", "isolation", "revoked", "unapproved"]):
            return {
                "severity": UIRepairSeverity.HIGH.value,
                "risk_level": "HIGH",
                "finding_category": "OPERATIONAL_INTEGRITY"
            }
            
        # 3. MEDIUM
        if any(k in control_key or k in rationale for k in ["drift", "trust-score", "degraded", "missing-hash"]):
            return {
                "severity": UIRepairSeverity.MEDIUM.value,
                "risk_level": "MEDIUM",
                "finding_category": "POLICY_AND_TRUST"
            }
            
        # 4. LOW (Default)
        return {
            "severity": UIRepairSeverity.LOW.value,
            "risk_level": "LOW",
            "finding_category": "CONFIG_HYGIENE"
        }
