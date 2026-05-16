import uuid
from typing import List, Optional, Dict, Any
from libs.db.models.ui_repair_models import IncidentSource, IncidentSeverity

class BusinessImpactScorer:
    def calculate_scores(self, source_type: IncidentSource, blast_radius: Dict[str, Any], 
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Calculates business_impact_score and executive_risk_score (0.0 - 100.0).
        """
        # Base scores by source type
        base_scores = {
            IncidentSource.SECURITY_POSTURE_FINDING: 40.0,
            IncidentSource.RED_TEAM_FINDING: 50.0,
            IncidentSource.COGNITIVE_INTEGRITY_BLOCK: 60.0,
            IncidentSource.IDENTITY_VIOLATION: 80.0,
            IncidentSource.TOOL_POLICY_VIOLATION: 70.0,
            IncidentSource.TENANT_ISOLATION_VIOLATION: 95.0,
            IncidentSource.MESH_FAILOVER: 30.0,
            IncidentSource.SLO_BREACH: 20.0,
            IncidentSource.COST_ANOMALY: 15.0,
            IncidentSource.GOVERNANCE_BYPASS_ATTEMPT: 90.0,
            IncidentSource.EVIDENCE_CHAIN_FAILURE: 85.0,
            IncidentSource.REMEDIATION_FAILURE: 45.0,
        }

        base_score = base_scores.get(source_type, 50.0)
        
        # Multipliers based on blast radius
        tenant_count = len(blast_radius.get("affected_tenants", []))
        tenant_multiplier = 1.0 + (min(tenant_count, 10) * 0.1)
        
        cross_tenant_penalty = 1.5 if blast_radius.get("cross_tenant_risk") else 1.0
        governance_penalty = 1.3 if blast_radius.get("governance_impact") else 1.0
        
        impact_score = base_score * tenant_multiplier * cross_tenant_penalty * governance_penalty
        impact_score = min(impact_score, 100.0)
        
        # Executive risk score is influenced by impact but also by remediation complexity/visibility
        risk_multiplier = 1.0
        if metadata:
            if metadata.get("remediation_complexity") == "HIGH":
                risk_multiplier += 0.2
            if metadata.get("executive_visibility") == "REQUIRED":
                risk_multiplier += 0.3
        
        executive_risk_score = min(impact_score * risk_multiplier, 100.0)
        
        return {
            "business_impact_score": round(impact_score, 2),
            "executive_risk_score": round(executive_risk_score, 2)
        }

    def determine_severity(self, scores: Dict[str, float]) -> IncidentSeverity:
        risk_score = scores.get("executive_risk_score", 0.0)
        
        if risk_score >= 85.0:
            return IncidentSeverity.P0_CRITICAL
        elif risk_score >= 60.0:
            return IncidentSeverity.P1_HIGH
        elif risk_score >= 30.0:
            return IncidentSeverity.P2_MEDIUM
        else:
            return IncidentSeverity.P3_LOW
        
