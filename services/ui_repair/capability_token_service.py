import uuid
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UICapabilityToken

class CapabilityTokenService:
    """Phase 19: Issues short-lived authorization tokens for specific actions."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def issue_token(
        self, 
        identity_key: str, 
        scope: Dict[str, Any], 
        actions: List[str], 
        duration_minutes: int = 60,
        issuer: str = "identity_service"
    ) -> UICapabilityToken:
        
        token_id = str(uuid.uuid4())
        # Simulate a secure token string (in production this would be a signed JWT)
        raw_token = f"{identity_key}:{token_id}:{datetime.now(timezone.utc).timestamp()}"
        evidence_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        token = UICapabilityToken(
            id=uuid.uuid4(),
            token_id=token_id,
            subject_identity_key=identity_key,
            scope_json=scope,
            allowed_actions_json=actions,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=duration_minutes),
            issued_by=issuer,
            evidence_hash=evidence_hash
        )
        self.db_session.add(token)
        await self.db_session.commit()
        return token

    async def validate_token(self, token_id: str, action: str, scope: Dict[str, Any]) -> Tuple[bool, str]:
        res = await self.db_session.execute(
            select(UICapabilityToken).where(UICapabilityToken.token_id == token_id)
        )
        token = res.scalars().first()
        
        if not token:
            return False, "Token not found"
        
        if token.revoked_at:
            return False, "Token has been revoked"
        
        if datetime.now(timezone.utc) > token.expires_at:
            return False, "Token has expired (STALE_TOKEN)"
        
        if action not in token.allowed_actions_json:
            return False, f"Action '{action}' not permitted by this token"
        
        # Scope check (tenant/project/cluster)
        for key, val in scope.items():
            if token.scope_json.get(key) != val:
                return False, f"Scope mismatch for '{key}': expected {token.scope_json.get(key)}"
        
        return True, "Valid"

    async def revoke_token(self, token_id: str):
        res = await self.db_session.execute(
            select(UICapabilityToken).where(UICapabilityToken.token_id == token_id)
        )
        token = res.scalars().first()
        if token:
            token.revoked_at = datetime.now(timezone.utc)
            await self.db_session.commit()
            return True
        return False
