import hashlib
import uuid
from typing import Any, Dict, Optional, Set, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UIAgentHandshake, HandshakeStatus, UISovereignIdentity, IdentityStatus
)
from services.ui_repair.sovereign_identity_registry import SovereignIdentityRegistry

class ZeroTrustHandshake:
    """Phase 19: Protocol for verifying agent-to-agent interactions."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.registry = SovereignIdentityRegistry(db_session)

    async def verify_handshake(self, request: Dict[str, Any]) -> Tuple[bool, str, Optional[UIAgentHandshake]]:
        source_key = request["source_identity_key"]
        target_key = request["target_identity_key"]
        nonce = request["nonce"]
        action = request["action_type"]
        
        # 1. Verify Identities
        source = await self.registry.get_identity(source_key)
        target = await self.registry.get_identity(target_key)
        
        if not source or not target:
            return False, "UNKNOWN_IDENTITY", None
        
        if source.status != IdentityStatus.ACTIVE or target.status != IdentityStatus.ACTIVE:
            return False, "IDENTITY_SUSPENDED", None

        # 2. Scope Check
        if source.tenant_key != request["tenant_key"]:
            return False, "BLOCKED_BY_SCOPE", None

        # 3. Nonce Check (Simple uniqueness for now)
        existing_nonce = await self.db_session.execute(
            select(UIAgentHandshake).where(UIAgentHandshake.nonce == nonce)
        )
        if existing_nonce.scalars().first():
            return False, "BLOCKED_BY_REPLAY_GUARD", None

        # 4. Handshake Success
        handshake = UIAgentHandshake(
            id=uuid.uuid4(),
            source_identity_key=source_key,
            target_identity_key=target_key,
            handshake_status=HandshakeStatus.PASSED,
            nonce=nonce,
            signed_context_hash=request.get("signature", "N/A"),
            tenant_key=request["tenant_key"],
            project_key=request["project_key"],
            cluster_key=request["cluster_key"],
            action_type=action,
            risk_level=request.get("risk_level", "LOW")
        )
        self.db_session.add(handshake)
        await self.db_session.commit()
        
        return True, "PASSED", handshake

class ReplayAttackGuard:
    """Simple in-memory cache for nonces to prevent immediate replay."""
    _used_nonces: Set[str] = set()

    @classmethod
    def is_nonce_valid(cls, nonce: str) -> bool:
        if nonce in cls._used_nonces:
            return False
        cls._used_nonces.add(nonce)
        # In production, this would expire nonces after a timeout
        return True
