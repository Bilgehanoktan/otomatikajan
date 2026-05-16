import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from libs.db.models.ui_repair_models import UIAttackSurfaceAsset, AssetType

logger = logging.getLogger(__name__)

class AttackSurfaceInventory:
    """Phase 23: Logic for discovering and classifying system assets."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def scan_system_assets(self, tenant_key: Optional[str] = None) -> List[UIAttackSurfaceAsset]:
        """
        Scans the system to discover critical assets across all layers.
        In a real scenario, this would query various registries (TenantRegistry, IdentityProvider, etc.).
        For now, we simulate discovery based on existing known structures.
        """
        logger.info(f"Starting attack surface scan for tenant: {tenant_key or 'GLOBAL'}")
        
        # Clear existing assets for the scope to avoid duplicates during re-scan
        # In production, we might want to update instead of delete
        
        discovered_assets = []
        
        # 1. Discover Tenants (Simulated)
        tenants = ["CORE_PLATFORM", "ALPHA_CORP", "BETA_SYSTEMS"]
        for t in tenants:
            if tenant_key and t != tenant_key:
                continue
            asset = UIAttackSurfaceAsset(
                asset_key=f"tenant:{t}",
                asset_type=AssetType.TENANT.value,
                tenant_key=t,
                exposure_level="MEDIUM",
                criticality="HIGH",
                metadata_json={"description": f"Main isolation boundary for {t}"}
            )
            discovered_assets.append(asset)
            
        # 2. Discover Identities (Simulated)
        identities = [
            {"key": "admin_service", "type": "SERVICE_ACCOUNT", "tenant": "CORE_PLATFORM"},
            {"key": "repair_agent_01", "type": "AGENT", "tenant": "CORE_PLATFORM"},
            {"key": "user_operator_alpha", "type": "USER", "tenant": "ALPHA_CORP"}
        ]
        for ident in identities:
            if tenant_key and ident["tenant"] != tenant_key:
                continue
            asset = UIAttackSurfaceAsset(
                asset_key=f"identity:{ident['key']}",
                asset_type=AssetType.IDENTITY.value,
                tenant_key=ident["tenant"],
                exposure_level="LOW",
                criticality="CRITICAL" if ident["type"] == "SERVICE_ACCOUNT" else "HIGH",
                metadata_json={"identity_type": ident["type"]}
            )
            discovered_assets.append(asset)

        # 3. Discover Tools & MCP Servers (Simulated)
        tools = [
            {"key": "git_patch_tool", "type": "EXTERNAL_TOOL", "tenant": "CORE_PLATFORM"},
            {"key": "k8s_mcp_server", "type": "MCP_SERVER", "tenant": "CORE_PLATFORM"},
            {"key": "compliance_auditor_tool", "type": "EXTERNAL_TOOL", "tenant": "BETA_SYSTEMS"}
        ]
        for tool in tools:
            if tenant_key and tool["tenant"] != tenant_key:
                continue
            asset = UIAttackSurfaceAsset(
                asset_key=f"tool:{tool['key']}",
                asset_type=tool["type"],
                tenant_key=tool["tenant"],
                exposure_level="MEDIUM",
                criticality="HIGH",
                metadata_json={"tool_type": tool["type"]}
            )
            discovered_assets.append(asset)

        # 4. Discover Policy Rules (Simulated)
        policies = [
            {"key": "deny_cross_tenant_access", "domain": "ISOLATION", "tenant": "CORE_PLATFORM"},
            {"key": "require_mfa_for_critical_tools", "domain": "IDENTITY", "tenant": "CORE_PLATFORM"},
            {"key": "audit_all_mcp_writes", "domain": "GOVERNANCE", "tenant": "CORE_PLATFORM"}
        ]
        for pol in policies:
            if tenant_key and pol["tenant"] != tenant_key:
                continue
            asset = UIAttackSurfaceAsset(
                asset_key=f"policy:{pol['key']}",
                asset_type=AssetType.POLICY_RULE.value,
                tenant_key=pol["tenant"],
                exposure_level="LOW",
                criticality="CRITICAL",
                metadata_json={"domain": pol["domain"]}
            )
            discovered_assets.append(asset)

        # Persist discovered assets
        for asset in discovered_assets:
            # Check if exists
            stmt = select(UIAttackSurfaceAsset).where(UIAttackSurfaceAsset.asset_key == asset.asset_key)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.exposure_level = asset.exposure_level
                existing.criticality = asset.criticality
                existing.metadata_json = asset.metadata_json
                existing.updated_at = datetime.utcnow()
            else:
                self.session.add(asset)
        
        await self.session.commit()
        return discovered_assets

    async def get_inventory(self, tenant_key: Optional[str] = None) -> List[UIAttackSurfaceAsset]:
        stmt = select(UIAttackSurfaceAsset)
        if tenant_key:
            stmt = stmt.where(UIAttackSurfaceAsset.tenant_key == tenant_key)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
