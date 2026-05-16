import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UISovereignIdentity, IdentityType, IdentityStatus, UITrustScore
)

class SovereignIdentityRegistry:
    """Phase 19: Central registry for all Sovereign AGI identities."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def register_identity(self, data: Dict[str, Any]) -> UISovereignIdentity:
        identity = UISovereignIdentity(
            id=uuid.uuid4(),
            identity_key=data["identity_key"],
            identity_type=data["identity_type"],
            display_name=data["display_name"],
            tenant_key=data.get("tenant_key", "GLOBAL"),
            project_key=data.get("project_key", "GLOBAL"),
            cluster_key=data.get("cluster_key", "GLOBAL"),
            allowed_actions_json=data.get("allowed_actions", []),
            trust_level=data.get("trust_level", "STANDARD"),
            status=IdentityStatus.ACTIVE,
            public_key_fingerprint=data.get("fingerprint", "N/A")
        )
        self.db_session.add(identity)
        
        # Initialize trust score
        trust = UITrustScore(
            id=uuid.uuid4(),
            identity_key=identity.identity_key,
            trust_score=1.0
        )
        self.db_session.add(trust)
        
        await self.db_session.commit()
        return identity

    async def get_identity(self, identity_key: str) -> Optional[UISovereignIdentity]:
        res = await self.db_session.execute(
            select(UISovereignIdentity).where(UISovereignIdentity.identity_key == identity_key)
        )
        return res.scalars().first()

    async def list_identities(self, tenant_key: Optional[str] = None) -> List[UISovereignIdentity]:
        stmt = select(UISovereignIdentity)
        if tenant_key:
            stmt = stmt.where(UISovereignIdentity.tenant_key == tenant_key)
        res = await self.db_session.execute(stmt)
        return list(res.scalars().all())

    async def update_status(self, identity_key: str, status: IdentityStatus) -> bool:
        identity = await self.get_identity(identity_key)
        if identity:
            identity.status = status
            await self.db_session.commit()
            return True
        return False

    async def seed_identities(self):
        """Seed default identities for Phase 19 bootstrap."""
        defaults = [
            {"identity_key": "stagehand_agent", "identity_type": IdentityType.AGENT, "display_name": "Stagehand Browser Agent"},
            {"identity_key": "openswe_agent", "identity_type": IdentityType.AGENT, "display_name": "OpenSWE Repair Agent"},
            {"identity_key": "pr_agent", "identity_type": IdentityType.AGENT, "display_name": "PR-Agent Reviewer"},
            {"identity_key": "verifier_mesh", "identity_type": IdentityType.AGENT, "display_name": "Verifier Mesh Auditor"},
            {"identity_key": "playwright_tool", "identity_type": IdentityType.TOOL, "display_name": "Playwright Engine"},
            {"identity_key": "default_worker", "identity_type": IdentityType.WORKER, "display_name": "Global Repair Worker"}
        ]
        
        for item in defaults:
            existing = await self.get_identity(item["identity_key"])
            if not existing:
                await self.register_identity(item)
