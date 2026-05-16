import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from libs.db.models.ui_repair_models import IncidentSource

class IncidentCommanderRecommender:
    def __init__(self, db: Session):
        self.db = db

    def recommend(self, source_type: IncidentSource, tenant_key: Optional[str] = None, 
                  project_key: Optional[str] = None) -> Dict[str, str]:
        """
        Recommends an Incident Commander and Owner Team based on the incident context.
        """
        # Mapping source types to functional owners
        domain_owners = {
            IncidentSource.SECURITY_POSTURE_FINDING: ("Security Operations", "SecOps_Agent_Alpha"),
            IncidentSource.RED_TEAM_FINDING: ("Red Team Command", "Adversarial_Orchestrator"),
            IncidentSource.COGNITIVE_INTEGRITY_BLOCK: ("AI Ethics & Integrity", "Cognitive_Guardian"),
            IncidentSource.IDENTITY_VIOLATION: ("Identity Management", "SIF01_Identity_Master"),
            IncidentSource.TOOL_POLICY_VIOLATION: ("Integration Governance", "Tool_Gatekeeper"),
            IncidentSource.TENANT_ISOLATION_VIOLATION: ("Global Security", "Sovereign_Shield_Commander"),
            IncidentSource.MESH_FAILOVER: ("Platform Engineering", "Mesh_Resiliency_Pilot"),
            IncidentSource.SLO_BREACH: ("Site Reliability", "SRE_Optimizer"),
            IncidentSource.COST_ANOMALY: ("FinOps", "Budget_Watcher"),
            IncidentSource.GOVERNANCE_BYPASS_ATTEMPT: ("Central Governance", "Governance_Lead"),
            IncidentSource.EVIDENCE_CHAIN_FAILURE: ("Audit & Compliance", "Evidence_Steward"),
            IncidentSource.REMEDIATION_FAILURE: ("Autonomous Repair", "Repair_Orchestrator_V2"),
        }

        team, commander = domain_owners.get(source_type, ("General Operations", "Standard_Incident_Commander"))

        # Override for specific tenants/projects if needed
        if tenant_key == "SYSTEM_CORE":
            commander = "Core_System_Administrator"

        return {
            "recommended_commander": commander,
            "recommended_team": team,
            "rationale": f"Selected based on domain expertise for {source_type.value}"
        }
