import logging
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import UITenantProjectBinding, UIClusterProfile, UITenantProfile
from libs.db.models.core_models import OperationalIncident

logger = logging.getLogger(__name__)

class FederatedIncidentRouter:
    """
    Routes operational incidents to the correct tenant, cluster, or global owner.
    """

    @staticmethod
    async def route_incident(db: AsyncSession, incident_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Determines the correct recipient for an incident based on hierarchy."""
        stmt = select(OperationalIncident).where(OperationalIncident.id == incident_id)
        incident = (await db.execute(stmt)).scalar_one_or_none()
        
        if not incident:
            return {"status": "ERROR", "message": "Incident not found"}

        project_key = context.get("project_key")
        
        # 1. Resolve Hierarchy
        binding_stmt = select(UITenantProjectBinding).where(UITenantProjectBinding.project_key == project_key)
        binding = (await db.execute(binding_stmt)).scalar_one_or_none()
        
        tenant_key = binding.tenant_key if binding else None
        cluster_key = binding.cluster_key if binding else None

        # 2. Routing Logic
        routing_decision = "GLOBAL"
        if project_key:
            routing_decision = "PROJECT_OWNER"
        if cluster_key and incident.component in ["CLUSTER_HEALTH", "INFRASTRUCTURE"]:
            routing_decision = "CLUSTER_OWNER"
        if tenant_key and incident.severity in ["HIGH", "CRITICAL"]:
            routing_decision = "TENANT_GOVERNANCE"
        
        # Special case for isolation breaches
        if incident.component == "TENANT_ISOLATION_GUARD":
            routing_decision = "GLOBAL_SECURITY"

        # 3. Update Incident Metadata
        meta = incident.metadata_json or {}
        meta.update({
            "routed_to": routing_decision,
            "tenant_key": tenant_key,
            "cluster_key": cluster_key,
            "project_key": project_key
        })
        incident.metadata_json = meta
        
        await db.commit()
        logger.info(f"Incident {incident_id} routed to {routing_decision}")
        
        return {
            "status": "SUCCESS",
            "routed_to": routing_decision,
            "tenant_key": tenant_key,
            "cluster_key": cluster_key
        }
