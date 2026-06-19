import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UITenantProfile, UITenantProjectBinding, UIClusterProfile
)
from services.ui_repair.schemas import (
    UITenantProfileCreate, UITenantProjectBindingCreate
)

logger = logging.getLogger(__name__)

class TenantRegistry:
    """
    Manages multi-tenant organization profiles and their project bindings.
    """

    @staticmethod
    async def create_tenant(db: AsyncSession, data: UITenantProfileCreate) -> UITenantProfile:
        """Registers a new enterprise tenant."""
        tenant = UITenantProfile(
            tenant_key=data.tenant_key,
            tenant_name=data.tenant_name,
            status=data.status or "ACTIVE",
            governance_level=data.governance_level or "STANDARD",
            contact_info=data.contact_info or {},
            tenant_metadata=data.tenant_metadata or {}
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        logger.info(f"Tenant created: {tenant.tenant_key}")
        return tenant

    @staticmethod
    async def list_tenants(db: AsyncSession) -> List[UITenantProfile]:
        """Lists all registered tenants."""
        stmt = select(UITenantProfile)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_tenant(db: AsyncSession, tenant_key: str) -> Optional[UITenantProfile]:
        """Retrieves a tenant by its unique key."""
        stmt = select(UITenantProfile).where(UITenantProfile.tenant_key == tenant_key)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def bind_project_to_tenant(db: AsyncSession, data: UITenantProjectBindingCreate) -> UITenantProjectBinding:
        """Binds a project to a tenant and optionally a cluster."""
        # Verify tenant exists
        tenant_stmt = select(UITenantProfile).where(UITenantProfile.tenant_key == data.tenant_key)
        tenant = (await db.execute(tenant_stmt)).scalar_one_or_none()
        if not tenant:
            raise ValueError(f"Tenant {data.tenant_key} not found")

        # Verify cluster exists if provided
        if data.cluster_key:
            cluster_stmt = select(UIClusterProfile).where(UIClusterProfile.cluster_key == data.cluster_key)
            cluster = (await db.execute(cluster_stmt)).scalar_one_or_none()
            if not cluster:
                raise ValueError(f"Cluster {data.cluster_key} not found")

        binding = UITenantProjectBinding(
            tenant_key=data.tenant_key,
            cluster_key=data.cluster_key,
            project_key=data.project_key,
            binding_status="ACTIVE"
        )
        db.add(binding)
        await db.commit()
        await db.refresh(binding)
        logger.info(f"Project {data.project_key} bound to tenant {data.tenant_key}")
        return binding

    @staticmethod
    async def get_project_binding(db: AsyncSession, project_key: str) -> Optional[UITenantProjectBinding]:
        """Gets the tenant/cluster binding for a specific project."""
        stmt = select(UITenantProjectBinding).where(UITenantProjectBinding.project_key == project_key)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_tenant_projects(db: AsyncSession, tenant_key: str) -> List[str]:
        """Lists project keys associated with a tenant."""
        stmt = select(UITenantProjectBinding.project_key).where(UITenantProjectBinding.tenant_key == tenant_key)
        result = await db.execute(stmt)
        return list(result.scalars().all())
