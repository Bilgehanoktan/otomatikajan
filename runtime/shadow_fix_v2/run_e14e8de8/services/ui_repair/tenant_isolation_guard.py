import logging
from typing import Optional, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import UITenantProjectBinding, UIRepairCase
from libs.db.models.core_models import SovereignEvidence, OperationalIncident

logger = logging.getLogger(__name__)

class TenantIsolationGuard:
    """
    Prevents data leakage between tenants by enforcing strict boundary checks.
    """

    @staticmethod
    async def validate_project_access(db: AsyncSession, tenant_key: str, project_key: str) -> bool:
        """Verifies if a tenant has access to a specific project."""
        if tenant_key == "GLOBAL_ADMIN":
            return True

        stmt = select(UITenantProjectBinding).where(
            (UITenantProjectBinding.tenant_key == tenant_key) &
            (UITenantProjectBinding.project_key == project_key)
        )
        binding = (await db.execute(stmt)).scalar_one_or_none()
        
        if not binding:
            await TenantIsolationGuard._log_violation(
                db, tenant_key, f"Unauthorized access attempt to project: {project_key}"
            )
            return False
        return True

    @staticmethod
    async def validate_resource_access(db: AsyncSession, tenant_key: str, resource_type: str, resource_id: Any) -> bool:
        """Verifies if a tenant has access to a specific resource (Case, Evidence, etc.)."""
        if tenant_key == "GLOBAL_ADMIN":
            return True

        # Resource-specific logic
        if resource_type == "CASE":
            stmt = select(UIRepairCase).where(UIRepairCase.id == resource_id)
            resource = (await db.execute(stmt)).scalar_one_or_none()
            if resource and resource.tenant_key != tenant_key:
                await TenantIsolationGuard._log_violation(
                    db, tenant_key, f"Tenant isolation breach: Attempted to access Case {resource_id} owned by {resource.tenant_key}"
                )
                return False
        
        elif resource_type == "EVIDENCE":
            stmt = select(SovereignEvidence).where(SovereignEvidence.id == resource_id)
            resource = (await db.execute(stmt)).scalar_one_or_none()
            # Note: Evidence might not have tenant_key directly in all versions, 
            # but we can check the payload or linked case
            if resource:
                payload = resource.payload or {}
                res_tenant = payload.get("tenant_key")
                if res_tenant and res_tenant != tenant_key:
                    await TenantIsolationGuard._log_violation(
                        db, tenant_key, f"Tenant isolation breach: Attempted to access Evidence {resource_id} owned by {res_tenant}"
                    )
                    return False

        return True

    @staticmethod
    async def _log_violation(db: AsyncSession, tenant_key: str, message: str):
        """Logs a tenant isolation violation to the governance and incident chains."""
        logger.warning(f"ISOLATION_VIOLATION: Tenant={tenant_key} | {message}")
        
        # 1. Create Operational Incident
        incident = OperationalIncident(
            incident_type="ISOLATION_VIOLATION",
            severity="HIGH",
            message=f"Tenant {tenant_key} attempted an unauthorized action: {message}",
            status="OPEN"
        )
        db.add(incident)
        
        # 2. Record in Sovereign Evidence
        evidence = SovereignEvidence(
            evidence_type="ISOLATION_VIOLATION",
            severity="high",
            payload={
                "tenant_key": tenant_key,
                "violation": message,
                "action": "BLOCKED_BY_TENANT_ISOLATION"
            }
        )
        db.add(evidence)
        await db.commit()
