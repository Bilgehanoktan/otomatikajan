import hmac
import hashlib
import secrets
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from apps.bilgeapi.repositories.interface import ApiKeyRepository
from apps.bilgeapi.services.audit import AuditService

logger = logging.getLogger("bilgeapi.api_key")

class ApiKeyService:
    def __init__(self, repo: ApiKeyRepository, audit_service: AuditService):
        self.repo = repo
        self.audit_service = audit_service

    async def generate_api_key(
        self,
        role: str,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        actor_id: str = "system",
        quota_daily: Optional[int] = None,
        quota_monthly: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a new secure database-backed API key."""
        # Generate the plaintext key (prefix + 32-byte secure token)
        plaintext_key = f"blg_live_{secrets.token_urlsafe(32)}"
        key_prefix = "blg_live_"
        
        # Compute SHA-256 hash
        key_hash = hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()
        
        # Compute fingerprint (first 12 characters of the hash)
        key_fingerprint = key_hash[:12]
        
        # Calculate expiration date
        expires_at = None
        if expires_in_days is not None and expires_in_days > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        key_id = f"key_{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc)

        key_data = {
            "id": key_id,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "key_fingerprint": key_fingerprint,
            "role": role,
            "description": description,
            "tenant_id": tenant_id,
            "is_active": True,
            "created_by": actor_id,
            "expires_at": expires_at,
            "created_at": created_at,
            "revoked_by": None,
            "revoke_reason": None,
            "revoked_at": None,
            "last_used_at": None,
            "quota_daily": quota_daily,
            "quota_monthly": quota_monthly
        }

        # Save to DB via repository
        saved_key = await self.repo.create(key_data)

        # Audit log creation
        # Using 'fingerprint' to avoid 'key' prefix redaction in AuditService
        await self.audit_service.log_event(
            event_type="API_KEY_CREATED",
            actor_id=actor_id,
            actor_type="operator" if actor_id != "system" else "system",
            entity_type="api_key",
            entity_id=key_id,
            metadata={
                "fingerprint": key_fingerprint,
                "prefix": key_prefix,
                "role": role,
                "description": description,
                "tenant_id": tenant_id
            }
        )

        # Inject plaintext key ONLY for creation response
        saved_key_with_plaintext = saved_key.copy()
        saved_key_with_plaintext["plaintext_key"] = plaintext_key
        return saved_key_with_plaintext

    async def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get(key_id)

    async def get_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_by_hash(key_hash)

    async def list_keys(self) -> List[Dict[str, Any]]:
        return await self.repo.list_all()

    async def revoke_api_key(self, key_id: str, actor_id: str, reason: str) -> Optional[Dict[str, Any]]:
        """Revoke an API key."""
        revoked_key = await self.repo.revoke(key_id, actor_id, reason)
        if revoked_key:
            # Audit log revocation
            await self.audit_service.log_event(
                event_type="API_KEY_REVOKED",
                actor_id=actor_id,
                actor_type="operator" if actor_id != "system" else "system",
                entity_type="api_key",
                entity_id=key_id,
                metadata={
                    "fingerprint": revoked_key["key_fingerprint"],
                    "reason": reason
                }
            )
        return revoked_key

    async def validate_key_and_record_use(
        self,
        plaintext_key: str,
        path: str,
        method: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        log_not_found_failure: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Validate the API key and update last_used_at best-effort with throttling."""
        # Clean prefix check if any
        if not plaintext_key:
            return None

        # Compute hash
        key_hash = hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()
        key_fingerprint = key_hash[:12]

        # Fetch key from DB using highly-efficient indexed lookup
        key_data = await self.repo.get_by_hash(key_hash)

        if not key_data:
            if log_not_found_failure:
                await self.audit_service.log_event(
                    event_type="API_KEY_AUTH_FAILED",
                    actor_id="unauthenticated",
                    actor_type="anonymous",
                    entity_type="security_gate",
                    entity_id=path,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={"reason": "invalid_api_key", "path": path, "method": method}
                )
            return None

        # Check status
        if not key_data.get("is_active"):
            await self.audit_service.log_event(
                event_type="API_KEY_AUTH_FAILED",
                actor_id="unauthenticated",
                actor_type="anonymous",
                entity_type="security_gate",
                entity_id=path,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "reason": "revoked_api_key",
                    "fingerprint": key_fingerprint,
                    "path": path,
                    "method": method
                }
            )
            return None

        # Check expiration
        expires_at = key_data.get("expires_at")
        if expires_at:
            # Make sure comparing same timezone info
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if datetime.now(timezone.utc) > expires_at:
                await self.audit_service.log_event(
                    event_type="API_KEY_EXPIRED",
                    actor_id=key_data["id"],
                    actor_type="system",
                    entity_type="api_key",
                    entity_id=key_data["id"],
                    metadata={"fingerprint": key_fingerprint}
                )
                await self.audit_service.log_event(
                    event_type="API_KEY_AUTH_FAILED",
                    actor_id="unauthenticated",
                    actor_type="anonymous",
                    entity_type="security_gate",
                    entity_id=path,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "reason": "expired_api_key",
                        "fingerprint": key_fingerprint,
                        "path": path,
                        "method": method
                    }
                )
                return None

        # Valid Key: Throttled update of last_used_at (maximum once per 60 seconds)
        last_used = key_data.get("last_used_at")
        should_update = False
        if not last_used:
            should_update = True
        else:
            if last_used.tzinfo is None:
                last_used = last_used.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - last_used
            if delta.total_seconds() > 60:
                should_update = True

        if should_update:
            await self._best_effort_update_last_used(key_data["id"])

        # Audit log key usage
        await self.audit_service.log_event(
            event_type="API_KEY_USED",
            actor_id=key_data["id"],
            actor_type="system",
            entity_type="api_key",
            entity_id=key_data["id"],
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "fingerprint": key_fingerprint,
                "role": key_data["role"],
                "path": path,
                "method": method
            }
        )

        return key_data

    async def _best_effort_update_last_used(self, key_id: str):
        try:
            await self.repo.update_last_used(key_id, datetime.now(timezone.utc))
        except Exception as e:
            logger.error(f"Best-effort last_used_at update failed: {e}")

    async def update_quota(
        self,
        key_id: str,
        quota_daily: Optional[int],
        quota_monthly: Optional[int],
        actor_id: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """Update quota limits for an API key."""
        updated_key = await self.repo.update_quota(key_id, quota_daily, quota_monthly)
        if updated_key:
            await self.audit_service.log_event(
                event_type="API_KEY_QUOTA_UPDATED",
                actor_id=actor_id,
                actor_type="operator" if actor_id != "system" else "system",
                entity_type="api_key",
                entity_id=key_id,
                metadata={
                    "fingerprint": updated_key["key_fingerprint"],
                    "quota_daily": quota_daily,
                    "quota_monthly": quota_monthly
                }
            )
        return updated_key
