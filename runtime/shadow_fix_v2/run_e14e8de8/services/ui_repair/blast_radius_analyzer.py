import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from libs.db.models.ui_repair_models import IncidentSource

class BlastRadiusAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def analyze(self, source_type: IncidentSource, source_id: uuid.UUID, 
                tenant_key: Optional[str] = None, project_key: Optional[str] = None, 
                cluster_key: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculates the affected entities and the scope of the incident.
        """
        affected_tenants = [tenant_key] if tenant_key else []
        affected_projects = [project_key] if project_key else []
        affected_clusters = [cluster_key] if cluster_key else []
        
        impacted_identities = []
        impacted_tools = []
        impacted_policies = []
        
        # Heuristics for blast radius expansion
        cross_tenant_risk = False
        governance_impact = False
        
        if source_type == IncidentSource.TENANT_ISOLATION_VIOLATION:
            cross_tenant_risk = True
            # In a real system, we'd query which other tenants might be reachable
            affected_tenants.append("TENANT_SCOPE_EXPANDED")
            
        if source_type in [IncidentSource.GOVERNANCE_BYPASS_ATTEMPT, IncidentSource.EVIDENCE_CHAIN_FAILURE]:
            governance_impact = True

        if metadata:
            if "identities" in metadata:
                impacted_identities.extend(metadata["identities"])
            if "tools" in metadata:
                impacted_tools.extend(metadata["tools"])
            if "policies" in metadata:
                impacted_policies.extend(metadata["policies"])

        return {
            "affected_tenants": list(set(affected_tenants)),
            "affected_projects": list(set(affected_projects)),
            "affected_clusters": list(set(affected_clusters)),
            "impacted_identities": list(set(impacted_identities)),
            "impacted_tools": list(set(impacted_tools)),
            "impacted_policies": list(set(impacted_policies)),
            "cross_tenant_risk": cross_tenant_risk,
            "governance_impact": governance_impact,
            "total_entity_count": len(affected_tenants) + len(affected_projects) + len(affected_clusters)
        }
