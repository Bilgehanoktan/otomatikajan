import jwt
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer
from apps.bilgeapi.config import settings
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.services.api_key import ApiKeyService
from apps.bilgeapi.services.quota import QuotaService, QuotaExceededError, get_quota_service_instance
from apps.bilgeapi.routers.deps import get_audit_service, get_api_key_service

logger = logging.getLogger("bilgeapi.auth")

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
jwt_scheme = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    "SOVEREIGN_PRIME": ["*"],
    "ADMIN": ["*"],
    "OPERATOR": [
        "bilgeapi.incident.read",
        "bilgeapi.incident.write",
        "bilgeapi.diagnostic.run",
        "bilgeapi.operator",
    ],
    "AUDIT_OBSERVER": [
        "bilgeapi.incident.read",
        "bilgeapi.audit.read",
    ]
}

def parse_static_keys() -> Dict[str, str]:
    """Parse settings.BILGEAPI_STATIC_KEYS into a dict mapping key to role.
    Supports 'key:role' format. Defaults role to 'OPERATOR' if omitted.
    """
    key_map = {}
    for entry in settings.BILGEAPI_STATIC_KEYS:
        if ":" in entry:
            parts = entry.split(":", 1)
            key_map[parts[0].strip()] = parts[1].strip().upper()
        else:
            key_map[entry.strip()] = "OPERATOR"
    return key_map

def parse_static_key_hashes() -> Dict[str, str]:
    """Parse settings.BILGEAPI_STATIC_KEY_HASHES into a dict mapping hash to role.
    Supports 'hash:role' format. Defaults role to 'OPERATOR' if omitted.
    """
    hash_map = {}
    for entry in settings.BILGEAPI_STATIC_KEY_HASHES:
        if ":" in entry:
            parts = entry.split(":", 1)
            hash_map[parts[0].strip()] = parts[1].strip().upper()
        else:
            hash_map[entry.strip()] = "OPERATOR"
    return hash_map

async def get_current_identity(
    request: Request,
    audit_service: AuditService = Depends(get_audit_service),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
    api_key_header: Optional[str] = Depends(api_key_scheme),
    jwt_header: Optional[Any] = Depends(jwt_scheme)
) -> dict:
    auth_mode = settings.BILGEAPI_AUTH_MODE
    
    if auth_mode == "disabled":
        identity = {
            "id": "disabled-auth",
            "name": "Bypassed Client",
            "role": "ADMIN",
            "type": "system",
            "tenant_id": "default"
        }
        request.state.identity = identity
        return identity
        
    if auth_mode == "api_key":
        api_key = request.headers.get("X-API-Key")
        key_roles = parse_static_keys()
        hash_roles = parse_static_key_hashes()
        
        if not api_key:
            err_msg = "Unauthorized: Missing API key"
            await audit_service.log_event(
                event_type="AUTH_FAILURE",
                actor_id="unauthenticated",
                actor_type="anonymous",
                entity_type="security_gate",
                entity_id=request.url.path,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"reason": err_msg, "path": request.url.path, "method": request.method}
            )
            raise HTTPException(status_code=401, detail=err_msg)
            
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # 1. DB-backed key validation (highest priority)
        db_key = None
        try:
            db_key = await api_key_service.validate_key_and_record_use(
                plaintext_key=api_key,
                path=request.url.path,
                method=request.method,
                ip_address=client_ip,
                user_agent=user_agent
            )
        except Exception as exc:
            logger.error(
                "DB-backed API key validation failed on %s %s: %s",
                request.method,
                request.url.path,
                exc,
            )
        if db_key:
            # ── Quota Enforcement (post-auth) ──
            quota_daily = db_key.get("quota_daily")
            quota_monthly = db_key.get("quota_monthly")
            has_quota = quota_daily is not None or quota_monthly is not None

            if has_quota:
                quota_svc = get_quota_service_instance(audit_service)
                try:
                    quota_info = await quota_svc.check_and_increment(
                        key_id=db_key["id"],
                        key_fingerprint=db_key["key_fingerprint"],
                        quota_daily=quota_daily,
                        quota_monthly=quota_monthly
                    )
                    # Stash for response header middleware
                    request.state.quota_info = quota_info
                except QuotaExceededError as qe:
                    from fastapi.responses import JSONResponse
                    reset_dt = qe.reset_at
                    # Calculate Retry-After as seconds until reset
                    try:
                        reset_time = datetime.fromisoformat(reset_dt)
                        retry_after = max(1, int((reset_time - datetime.now(timezone.utc)).total_seconds()))
                    except Exception:
                        retry_after = 60

                    headers = {
                        "X-RateLimit-Limit": str(qe.limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": reset_dt,
                        "Retry-After": str(retry_after)
                    }
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "detail": "Quota exceeded",
                            "scope": qe.scope,
                            "limit": qe.limit,
                            "used": qe.used,
                            "reset_at": reset_dt
                        },
                        headers=headers
                    )

            identity = {
                "id": db_key["id"],
                "name": db_key["description"] or "API Key Client",
                "role": db_key["role"].upper(),
                "type": "system",
                "key_id": db_key["id"],
                "key_fingerprint": db_key["key_fingerprint"],
                "tenant_id": db_key.get("tenant_id") or "default"
            }
            request.state.identity = identity
            return identity

        # 2. Check hashed keys fallback (preferred static)
        api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        matched_role = None
        for h, role in hash_roles.items():
            if hmac.compare_digest(api_key_hash, h):
                matched_role = role
                break

        # 3. Check plaintext keys fallback (only in non-production environments)
        if not matched_role and settings.APP_ENV != "production":
            for k, role in key_roles.items():
                if hmac.compare_digest(api_key, k):
                    matched_role = role
                    break

        if not matched_role:
            err_msg = "Unauthorized: Invalid API key"
            await audit_service.log_event(
                event_type="AUTH_FAILURE",
                actor_id="unauthenticated",
                actor_type="anonymous",
                entity_type="security_gate",
                entity_id=request.url.path,
                ip_address=client_ip,
                user_agent=user_agent,
                metadata={"reason": err_msg, "path": request.url.path, "method": request.method}
            )
            raise HTTPException(status_code=401, detail=err_msg)

        # Log usage of static key
        await audit_service.log_event(
            event_type="STATIC_API_KEY_USED",
            actor_id="static_key",
            actor_type="system",
            entity_type="security_gate",
            entity_id=request.url.path,
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={
                "fingerprint": api_key_hash[:12],
                "role": matched_role,
                "path": request.url.path,
                "method": request.method
            }
        )

        identity = {
            "id": f"api_key_{api_key_hash[:12]}",
            "name": "Static API Key Client",
            "role": matched_role,
            "type": "system",
            "tenant_id": "default"
        }
        request.state.identity = identity
        return identity

    if auth_mode == "jwt":
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        else:
            token = request.cookies.get("access_token")
            
        if not token:
            err_msg = "Oturum veya API Anahtarı gerekli"
            await audit_service.log_event(
                event_type="AUTH_FAILURE",
                actor_id="unauthenticated",
                actor_type="anonymous",
                entity_type="security_gate",
                entity_id=request.url.path,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"reason": err_msg, "path": request.url.path, "method": request.method}
            )
            raise HTTPException(status_code=401, detail=err_msg)
            
        payload = None
        last_err = None
        for secret in settings.BILGEAPI_JWT_SECRETS:
            try:
                payload = jwt.decode(token, secret, algorithms=["HS256"])
                break
            except jwt.ExpiredSignatureError as e:
                last_err = e
            except jwt.InvalidTokenError as e:
                last_err = e
                
        if not payload:
            err_msg = "Token süresi doldu" if isinstance(last_err, jwt.ExpiredSignatureError) else f"Geçersiz token: {str(last_err)}"
            await audit_service.log_event(
                event_type="AUTH_FAILURE",
                actor_id="unauthenticated",
                actor_type="anonymous",
                entity_type="security_gate",
                entity_id=request.url.path,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"reason": err_msg, "path": request.url.path, "method": request.method}
            )
            if isinstance(last_err, jwt.ExpiredSignatureError):
                raise HTTPException(status_code=401, detail="Token süresi doldu")
            else:
                raise HTTPException(status_code=401, detail="Geçersiz token")
                
        identity_id = payload.get("sub")
        if not identity_id:
            raise HTTPException(status_code=401, detail="Geçersiz token")
            
        identity = {
            "id": identity_id,
            "name": payload.get("name", payload.get("email", "Unknown")),
            "role": payload.get("role", "GUEST").upper(),
            "type": payload.get("identity_type", "operator"),
            "tenant_id": payload.get("tenant_id") or "default"
        }
        request.state.identity = identity
        return identity

    raise HTTPException(status_code=500, detail="Unsupported auth configuration")

def require_permission(permission: str):
    async def checker(
        request: Request,
        identity: dict = Depends(get_current_identity),
        audit_service: AuditService = Depends(get_audit_service)
    ) -> dict:
        auth_mode = settings.BILGEAPI_AUTH_MODE
        if auth_mode == "disabled":
            return identity
            
        role = identity.get("role", "GUEST")
        allowed_permissions = ROLE_PERMISSIONS.get(role, [])
        
        has_perm = "*" in allowed_permissions or permission in allowed_permissions
        if not has_perm:
            err_msg = f"SIF-03 ACCESS DENIED: Missing required permission '{permission}' for role '{role}'"
            await audit_service.log_event(
                event_type="RBAC_FAILURE",
                actor_id=identity["id"],
                actor_type=identity["type"],
                entity_type="security_gate",
                entity_id=request.url.path,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"reason": err_msg, "path": request.url.path, "method": request.method}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=err_msg
            )
            
        return identity
    return checker
