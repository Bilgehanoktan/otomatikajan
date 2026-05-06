"""
JWT Auth & Sovereign Identity Framework (SIF-01)
Supports Scoped Permissions + Operator/System Identity differentiation.
"""

import os
import secrets
import time
import logging
import uuid
import fnmatch
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Any, Optional, Union, List, Dict

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.session import get_db
from libs.db.models import Operator, SystemIdentity, PermissionGrant, RefreshToken
from libs.config import JWT_SECRET, APP_ENV

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
if not JWT_SECRET:
    JWT_SECRET = secrets.token_hex(64)

_DEFAULT_ACCESS_MIN = "1440" if APP_ENV in ("development", "local-dev") else "15"
ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_MINUTES", _DEFAULT_ACCESS_MIN))
REFRESH_DAYS   = int(os.getenv("JWT_REFRESH_DAYS", "7"))

_bearer = HTTPBearer(auto_error=False)

# ── Pydantic Modelleri ─────────────────────────────────────
class RegisterRequest(BaseModel):
    email:    str
    password: str
    username: Optional[str] = None

class LoginRequest(BaseModel):
    email:    str
    password: str

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    role:          str
    token_type:    str = "bearer"
    expires_in:    int = ACCESS_MINUTES * 60
    permissions:   List[str] = []

# ── Helper: Token Üretimi / Doğrulama ─────────────────────────────
def _make_token(payload: dict, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    data = {
        **payload, 
        "exp": int((now + expires_delta).timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()) # SIF-01 Enhancement: Unique token ID
    }
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _decode_token(token: str) -> dict:
    try:
        # SIF-01: Added leeway to prevent false-positives due to clock skew
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], leeway=30)
        return decoded
    except jwt.ExpiredSignatureError:
        logger.info("AUTH INFO: Access token expired.")
        raise HTTPException(status_code=401, detail="Token süresi doldu")
    except jwt.InvalidTokenError as e:
        logger.info(f"AUTH INFO: Invalid token ({type(e).__name__}).")
        raise HTTPException(status_code=401, detail="Geçersiz token")

# ── Cookie Yardımcıları ───────────────────────────────────
def set_auth_cookies(response: Response, access_token: str, refresh_token: str, request: Request = None):
    is_secure = APP_ENV == "production"
    if request:
        host = request.url.hostname or ""
        if host in ("localhost", "127.0.0.1") or request.url.scheme == "http":
            is_secure = False

    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_MINUTES * 60, samesite="lax", secure=is_secure)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=REFRESH_DAYS * 24 * 3600, samesite="lax", secure=is_secure)

def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

# ── Access Control Service (SIF-01) ──────────────────────
class AccessControlService:
    _PERMISSION_ALIASES: Dict[str, List[str]] = {
        "approval.decide": ["approveall.decide"],
        "approval.view": ["approveall.view"],
        "workflow.approve": ["approveall.decide"],
    }

    _BASELINE_ROLE_PERMISSIONS: Dict[str, List[str]] = {
        "SOVEREIGN_PRIME": ["*"],
        "ADMIN": ["*"],
        "OPERATOR": [
            "workflow.view",
            "workflow.create",
            "workflow.approve",
            "workflow.replay",
            "approveall.decide",
            "approval.view",
            "approval.decide",
            "approval.*",
            "incident.view",
            "incident.resolve",
            "incident.*",
            "governor.view",
            "governor.scan",
            "governor.execute",
            "governor.override",
            "governance.proof.view",
            "governance.proof.verify",
            "governance.proof.export",
            "governance.lineage.view",
            "learning.view",
            "governance.*",
            "mesh.*",
            "repair_lab.*",
        ],
        # Local control-plane operator experience:
        # observers can execute core governance actions in development baseline mode.
        "AUDIT_OBSERVER": [
            "*.view",
            "approval.decide",
            "incident.resolve",
            "workflow.approve",
            "workflow.replay",
        ],
        "GOVERNANCE_AGENT": [
            "workflow.view",
            "approveall.decide",
            "approval.view",
            "approval.decide",
            "approval.*",
            "incident.view",
            "incident.resolve",
            "incident.*",
            "governor.view",
            "governor.scan",
            "governance.proof.view",
            "governance.proof.verify",
            "learning.view",
            "governance.*",
        ],
    }

    @classmethod
    def _normalize_role(cls, role: str | None) -> str:
        return str(role or "").strip().upper()

    @classmethod
    def _baseline_enabled(cls) -> bool:
        raw = os.getenv("SIF_BASELINE_RBAC")
        if raw is not None and str(raw).strip() != "":
            return str(raw).strip().lower() in {"1", "true", "yes", "on"}
        return APP_ENV in ("development", "local-dev")

    @classmethod
    def _permission_candidates(cls, permission: str) -> List[str]:
        candidates = {permission}
        for canonical, aliases in cls._PERMISSION_ALIASES.items():
            alias_set = set(aliases)
            if permission == canonical:
                candidates.update(alias_set)
            elif permission in alias_set:
                candidates.add(canonical)
                candidates.update(alias_set)
        return sorted(candidates)

    @classmethod
    def _matches_permission_pattern(cls, permission: str, pattern: str) -> bool:
        if pattern == "*" or permission == pattern:
            return True
        if pattern.endswith(".*"):
            return permission.startswith(pattern[:-1])
        return fnmatch.fnmatch(permission, pattern)

    @classmethod
    def _has_baseline_permission(cls, role: str | None, permission: str) -> bool:
        normalized = cls._normalize_role(role)
        patterns = cls._BASELINE_ROLE_PERMISSIONS.get(normalized, [])
        permission_candidates = cls._permission_candidates(permission)
        return any(
            cls._matches_permission_pattern(candidate, pattern)
            for candidate in permission_candidates
            for pattern in patterns
        )

    @staticmethod
    async def is_allowed(
        db: AsyncSession, 
        identity_id: uuid.UUID, 
        identity_type: str, 
        permission: str, 
        scope_type: str = "global", 
        scope_value: str = "global",
        role: str = None
    ) -> tuple[bool, str]: # SIF-03: Now returns (allowed, reason)
        """
        Dinamik yetki kontrolü.
        Prime operatörler her şeye yetkilidir.
        """
        logger.error(f"[SIF-01] Access check: role={role}, permission={permission}, identity_type={identity_type}")
        normalized_role = AccessControlService._normalize_role(role)
        permission_candidates = AccessControlService._permission_candidates(permission)
        # 1. PRIME yetkisi kontrolü
        if normalized_role == "SOVEREIGN_PRIME":
            return True, "Override: PRIME privileges granted."

        # SIF-01: Base Observer Access
        if normalized_role == "AUDIT_OBSERVER" and permission.endswith(".view"):
            return True, "Authorized: View-only access granted for AUDIT_OBSERVER."

        # SIF-04: Autonomous Trust & Quarantine Response
        if identity_type == "system":
            res = await db.execute(select(SystemIdentity).where(SystemIdentity.id == identity_id))
            sys_id = res.scalar_one_or_none()
            if sys_id:
                if sys_id.quarantined_at:
                    return False, f"SIF-04: Identity QUARANTINED due to: {sys_id.risk_reason or 'Security Breach'}"
                if sys_id.risk_level == "CRITICAL" and not permission.endswith(".view"):
                    return False, "SIF-04: Autonomous write-lock active due to CRITICAL risk level."
                if sys_id.trust_score < 40 and permission.startswith("workflow."):
                    return False, f"SIF-04: Insufficient Trust Score ({sys_id.trust_score}) for sensitive operations."

        try:
            # 2. SIF-02: Check for ANY Explicit DENY first (Deny overrides everything)
            deny_query = select(PermissionGrant).where(
                and_(
                    PermissionGrant.operator_id == identity_id if identity_type == "operator" else PermissionGrant.system_id == identity_id,
                    PermissionGrant.permission.in_(permission_candidates),
                    PermissionGrant.effect == "deny"
                )
            )
            
            # Scope kontrolü (Deny için genişten dara doğru bak)
            if scope_type != "global":
                deny_query = deny_query.where(
                    or_(
                        PermissionGrant.scope_type == "global",
                        and_(PermissionGrant.scope_type == scope_type, PermissionGrant.scope_value == scope_value)
                    )
                )
            else:
                deny_query = deny_query.where(PermissionGrant.scope_type == "global")

            deny_res = await db.execute(deny_query)
            if deny_res.scalar_one_or_none():
                logger.info(f"[SIF-03] Deny rule triggered for {identity_id} on {permission}")
                return False, f"SIF-03: Access blocked by an Explicit Deny rule for '{permission}'"
        except Exception as e:
            logger.error(f"[SIF-03] Error checking deny rules: {str(e)}", exc_info=True)
            raise

        # 3. Check for ALLOW
        query = select(PermissionGrant).where(
                and_(
                    PermissionGrant.operator_id == identity_id if identity_type == "operator" else PermissionGrant.system_id == identity_id,
                    PermissionGrant.permission.in_(permission_candidates),
                    PermissionGrant.effect == "allow"
                )
            )
        
        # Scope kontrolü (En dardan en genişe bak: project -> global)
        if scope_type != "global":
            query = query.where(
                or_(
                    PermissionGrant.scope_type == "global",
                    and_(PermissionGrant.scope_type == scope_type, PermissionGrant.scope_value == scope_value)
                )
            )
        else:
            query = query.where(PermissionGrant.scope_type == "global")

        res = await db.execute(query)
        if res.scalar_one_or_none():
            return True, "Authorized via Permission Matrix (Allow/Alias)"

        if AccessControlService._baseline_enabled() and AccessControlService._has_baseline_permission(role, permission):
            return True, "Authorized via Baseline Role Policy"

        return False, f"Missing required permission '{permission}' for scope '{scope_type}:{scope_value}'"

# ── Auth Service ──────────────────────────────────────────
class AuthService:
    async def register(self, db: AsyncSession, email: str, password: str, username: str = None) -> Operator:
        from bcrypt import hashpw, gensalt
        existing = await db.execute(select(Operator).where(Operator.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı")

        if len(password) < 8:
            raise HTTPException(status_code=422, detail="Parola en az 8 karakter olmalıdır")

        hashed = hashpw(password.encode(), gensalt(rounds=12)).decode()
        operator = Operator(
            email=email, 
            username=username or email.split('@')[0], 
            hashed_password=hashed,
            role="AUDIT_OBSERVER"
        )
        db.add(operator)
        await db.flush()
        return operator

    async def login(self, db: AsyncSession, email: str, password: str) -> TokenResponse:
        from bcrypt import checkpw
        result = await db.execute(select(Operator).where(Operator.email == email))
        operator = result.scalar_one_or_none()

        if not operator or not checkpw(password.encode(), operator.hashed_password.encode()):
            raise HTTPException(status_code=401, detail="Hatalı e-posta veya parola")

        if not operator.is_active:
            raise HTTPException(status_code=403, detail="Hesap devre dışı")

        access = _make_token({
            "sub": str(operator.id),
            "email": operator.email,
            "type": "access",
            "identity_type": "operator",
            "role": operator.role
        }, timedelta(minutes=ACCESS_MINUTES))
        
        refresh = _make_token({"sub": str(operator.id), "type": "refresh"}, timedelta(days=REFRESH_DAYS))

        # Refresh token'ı kaydet
        rt = RefreshToken(user_id=operator.id, token=refresh, expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS))
        db.add(rt)
        await db.flush() # Catch IntegrityError early
        
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            role=operator.role,
            permissions=[] # Opsiyonel: Frontend için doldurulabilir
        )

    async def refresh(self, db: AsyncSession, refresh_token: str) -> TokenResponse:
        payload = _decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Geçersiz token tipi")

        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.revoked == False,
            )
        )
        rt = result.scalar_one_or_none()
        if not rt:
            raise HTTPException(status_code=401, detail="Refresh token geçersiz")

        rt.revoked = True
        await db.flush()

        res = await db.execute(select(Operator).where(Operator.id == rt.user_id))
        operator = res.scalar_one_or_none()
        if not operator or not operator.is_active:
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")

        access = _make_token({
            "sub": str(operator.id),
            "email": operator.email,
            "type": "access",
            "identity_type": "operator",
            "role": operator.role
        }, timedelta(minutes=ACCESS_MINUTES))
        
        new_refresh = _make_token({"sub": str(operator.id), "type": "refresh"}, timedelta(days=REFRESH_DAYS))
        new_rt = RefreshToken(user_id=operator.id, token=new_refresh, expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS))
        db.add(new_rt)
        await db.flush()

        return TokenResponse(
            access_token=access,
            refresh_token=new_refresh,
            role=operator.role
        )

    async def revoke_all(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        from sqlalchemy import update
        result = await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        return result.rowcount

    # SIF-02: API Key Lifecycle Management
    async def create_api_key(self, db: AsyncSession, identity_id: uuid.UUID, name: str) -> str:
        """Generates a new API Key and stores its hash."""
        import secrets
        from hashlib import sha256
        
        raw_key = f"sov_{secrets.token_urlsafe(32)}"
        key_hash = sha256(raw_key.encode()).hexdigest()
        
        # Update SystemIdentity with the new hash (Simplified for now)
        from sqlalchemy import update
        await db.execute(
            update(SystemIdentity)
            .where(SystemIdentity.id == identity_id)
            .values(api_key_hash=key_hash)
        )
        await db.commit()
        return raw_key

    async def get_identity_from_token(self, db: AsyncSession, token: str) -> Dict[str, Any]:
        try:
            payload = _decode_token(token)
            identity_id = uuid.UUID(payload["sub"])
            identity_type = payload.get("identity_type", "operator")
            
            if identity_type == "operator":
                res = await db.execute(select(Operator).where(Operator.id == identity_id))
                obj = res.scalar_one_or_none()
            else:
                res = await db.execute(select(SystemIdentity).where(SystemIdentity.id == identity_id))
                obj = res.scalar_one_or_none()

            if not obj or not obj.is_active:
                raise HTTPException(status_code=401, detail="Kimlik bulunamadı veya pasif")
            
            logger.debug(f"[AUTH] Identity resolved: {identity_id} (Type: {identity_type})")
            return {
                "id": obj.id,
                "obj": obj,
                "type": identity_type,
                "role": getattr(obj, "role", "GUEST"),
                "email": getattr(obj, "email", None),
                "name": getattr(obj, "name", getattr(obj, "username", "Unknown"))
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[AUTH] Critical error in get_identity_from_token: {str(e)}", exc_info=True)
            raise

auth_service = AuthService()
access_service = AccessControlService()

# ── FastAPI Depends ────────────────────────────────────────
async def get_current_identity(request: Request, db: AsyncSession = Depends(get_db)):
    # 1. API Key Check (for System Identities/Agents)
    api_key = request.headers.get("X-API-KEY")
    if api_key:
        # SRE Hardening: Simple hash check for now, can be extended to bcrypt
        from hashlib import sha256
        key_hash = sha256(api_key.encode()).hexdigest()
        
        res = await db.execute(select(SystemIdentity).where(SystemIdentity.api_key_hash == key_hash))
        sys_id = res.scalar_one_or_none()
        
        if sys_id and sys_id.is_active:
            # SIF-03: Update usage telemetry
            from datetime import datetime
            now = datetime.utcnow()
            
            # SIF-04: Burst Usage Detection & Trust Penalty
            if sys_id.last_used_at:
                # timezone farkını handle et
                last_used = sys_id.last_used_at
                if last_used.tzinfo:
                    from datetime import timezone
                    now_tz = datetime.now(timezone.utc)
                    diff = (now_tz - last_used).total_seconds()
                else:
                    diff = (now - last_used).total_seconds()

                if diff < 0.1: # Burst detection (10 req/sec)
                    sys_id.trust_score = max(0, sys_id.trust_score - 5)
                    sys_id.risk_level = "HIGH" if sys_id.trust_score < 60 else "MEDIUM"
                    
                    # Auto-Quarantine if trust is decimated
                    if sys_id.trust_score < 20:
                        sys_id.quarantined_at = now
                        sys_id.risk_level = "CRITICAL"
                        sys_id.risk_reason = "Autonomous Response: High-frequency burst abuse detected."

            sys_id.last_used_at = now
            await db.commit()
            
            return {
                "id": str(sys_id.id),
                "name": sys_id.name,
                "role": sys_id.role,
                "type": "system",
                "is_active": sys_id.is_active
            }
        elif sys_id:
            raise HTTPException(status_code=401, detail="Sistem kimliği pasif.")
        # Fallthrough to JWT if API Key is invalid (optional policy)

    # 2. JWT Check (for Operators)
    token = request.cookies.get("access_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        logger.debug(f"AUTH INFO: No token found in cookies or headers for {request.url.path}")
        raise HTTPException(status_code=401, detail="Oturum veya API Anahtarı gerekli")
    
    try:
        identity = await auth_service.get_identity_from_token(db, token)
        return identity
    except HTTPException as e:
        if request.url.path.endswith("/auth/me") or request.url.path.endswith("/auth/me/"):
            logger.debug("AUTH INFO: /auth/me unauthorized (%s).", e.detail)
        else:
            logger.info("AUTH INFO: Unauthorized request on %s (%s).", request.url.path, e.detail)
        raise e
    except Exception as e:
        logger.error(f"AUTH CRITICAL: Unexpected error in auth check: {e}")
        raise HTTPException(status_code=401, detail="Kimlik doğrulama sırasında beklenmedik hata")

def require_permission(permission: str, scope_type: str = "global"):
    """
    Kullanım: Depends(require_permission("workflow.execute"))
    """
    async def checker(request: Request, identity: dict = Depends(get_current_identity), db: AsyncSession = Depends(get_db)):
        try:
            # Scope value'yu request'ten (path param) çıkarmaya çalış
            scope_value = request.path_params.get("project_id") or request.path_params.get("id")
            # 3. Kapsamlı Yetki Kontrolü
            allowed, reason = await access_service.is_allowed(
                db, 
                identity_id=identity["id"],
                identity_type=identity["type"],
                permission=permission,
                scope_type=scope_type,
                scope_value=scope_value,
                role=identity["role"]
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"SIF-03 ACCESS DENIED: {reason}"
                )
            return identity
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[SIF-03] UNHANDLED ERROR in permission check: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Permission Check Failure: {str(e)}")
    return checker

# Legacy support for transitions
get_current_user = get_current_identity
