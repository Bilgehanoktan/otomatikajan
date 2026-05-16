import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIIdentityAuditEvent
from services.ui_repair.trust_score_engine import TrustScoreEngine
from services.ui_repair.sovereign_identity_registry import SovereignIdentityRegistry

class IdentityPolicyEnforcer:
    """Phase 19: Unified authorization gate for identities."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.registry = SovereignIdentityRegistry(db_session)
        self.trust_engine = TrustScoreEngine(db_session)

    async def authorize_action(self, identity_key: str, action: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        identity = await self.registry.get_identity(identity_key)
        if not identity:
            return False, "UNKNOWN_IDENTITY"
        
        if identity.status != "ACTIVE":
            return False, f"IDENTITY_{identity.status}"

        # 1. Trust Gate
        trust_score = await self.trust_engine.get_score(identity_key)
        if trust_score < 0.3 and action in ["APPLY_PATCH", "RUN_MCP_WRITE"]:
            return False, "TRUST_SCORE_TOO_LOW"

        # 2. Scope Gate
        if identity.tenant_key != context.get("tenant_key", "GLOBAL"):
            return False, "TENANT_SCOPE_MISMATCH"

        # 3. Action Capability
        if action not in identity.allowed_actions_json and "ALL" not in identity.allowed_actions_json:
            return False, "ACTION_NOT_PERMITTED"

        return True, "AUTHORIZED"

class IdentityAuditLedger:
    """Phase 19: Non-repudiable ledger for identity events."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def record_event(self, data: Dict[str, Any]):
        event = UIIdentityAuditEvent(
            id=uuid.uuid4(),
            identity_key=data["identity_key"],
            event_type=data["event_type"],
            action_type=data.get("action_type"),
            decision=data["decision"],
            reason=data.get("reason", ""),
            tenant_key=data.get("tenant_key", "GLOBAL"),
            project_key=data.get("project_key", "GLOBAL"),
            cluster_key=data.get("cluster_key", "GLOBAL"),
            evidence_hash=data.get("evidence_hash")
        )
        self.db_session.add(event)
        await self.db_session.commit()
        return event
