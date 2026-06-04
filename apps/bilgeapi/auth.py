import jwt
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer
from apps.bilgeapi.config import settings
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.routers.deps import get_audit_service

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

async def get_current_identity(
    request: Request,
    audit_service: AuditService = Depends(get_audit_service),
    api_key_header: Optional[str] = Depends(api_key_scheme),
    jwt_header: Optional[Any] = Depends(jwt_scheme)
) -> dict:
    auth_mode = settings.BILGEAPI_AUTH_MODE
    
    if auth_mode == "disabled":
        return {
            "id": "disabled-auth",
            "name": "Bypassed Client",
            "role": "ADMIN",
            "type": "system"
        }
        
    if auth_mode == "api_key":
        api_key = request.headers.get("X-API-Key")
        key_roles = parse_static_keys()
        
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
            
        if api_key not in key_roles:
            err_msg = "Unauthorized: Invalid API key"
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
            
        role = key_roles[api_key]
        return {
            "id": f"api_key_{api_key[:8]}" if len(api_key) > 8 else "api_key_short",
            "name": "API Key Client",
            "role": role,
            "type": "system"
        }

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
            
        try:
            payload = jwt.decode(token, settings.BILGEAPI_JWT_SECRET, algorithms=["HS256"])
            identity_id = payload.get("sub")
            if not identity_id:
                raise jwt.InvalidTokenError("Missing sub claim")
                
            return {
                "id": identity_id,
                "name": payload.get("name", payload.get("email", "Unknown")),
                "role": payload.get("role", "GUEST").upper(),
                "type": payload.get("identity_type", "operator")
            }
        except jwt.ExpiredSignatureError:
            err_msg = "Token süresi doldu"
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
        except jwt.InvalidTokenError as e:
            err_msg = f"Geçersiz token: {str(e)}"
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
            raise HTTPException(status_code=401, detail="Geçersiz token")

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
