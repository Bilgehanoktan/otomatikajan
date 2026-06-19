"""
Auth Router — /api/v1/auth prefix ile kayıtlı
SIF-01 (Sovereign Identity Framework) entegrasyonu.
"""

from typing import TYPE_CHECKING, Dict, Any
from fastapi import APIRouter, Depends, Response, Request, HTTPException, status

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
# SQLAlchemy imports moved to local scopes to prevent Phase 13.04 startup hangs in Python 3.14+
# from sqlalchemy import select
# from libs.db.models.auth_models import Operator, SystemIdentity
from libs.db.session import get_db
from services.auth.jwt_auth import get_current_identity, require_permission

router = APIRouter()


def _svc():
    """Lazy import for auth service components."""
    from services.auth.jwt_auth import (
        auth_service,
        RegisterRequest,
        LoginRequest,
        TokenResponse,
        set_auth_cookies,
        clear_auth_cookies,
    )
    return auth_service, RegisterRequest, LoginRequest, TokenResponse, set_auth_cookies, clear_auth_cookies


@router.post("/register", summary="Yeni operatör kaydı")
@router.post("/register/", include_in_schema=False)
async def register(body: dict, db: Any = Depends(get_db)):
    from libs.db.models.auth_models import Operator
    svc, _, _, _, _, _ = _svc()
    operator = await svc.register(db, body["email"], body["password"], body.get("username"))
    await db.commit()
    return {"id": str(operator.id), "email": operator.email, "role": operator.role}


@router.post("/login", summary="Giriş — token al")
@router.post("/login/", include_in_schema=False)
async def login(response: Response, request: Request, body: dict, db: "AsyncSession" = Depends(get_db)):
    svc, _, _, _, set_cookies, _ = _svc()
    email = body.get("email")
    password = body.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email ve parola gerekli")
        
    res = await svc.login(db, email, password)
    await db.commit()
    set_cookies(response, res.access_token, res.refresh_token, request=request)
    return res


@router.post("/refresh", summary="Access token yenile")
async def refresh(request: Request, response: Response, body: dict | None = None, db: "AsyncSession" = Depends(get_db)):
    svc, _, _, _, set_cookies, _ = _svc()
    rt = (body or {}).get("refresh_token") or request.cookies.get("refresh_token")
        
    if not rt:
        raise HTTPException(status_code=422, detail="refresh_token gerekli")
        
    res = await svc.refresh(db, rt)
    await db.commit()
    set_cookies(response, res.access_token, res.refresh_token, request=request)
    return res


@router.post("/logout", summary="Oturumu kapat")
@router.post("/logout/", include_in_schema=False)
async def logout(response: Response, identity: Dict[str, Any] = Depends(get_current_identity), db: "AsyncSession" = Depends(get_db)):
    svc, _, _, _, _, clear_cookies = _svc()
    await svc.revoke_all(db, identity["id"])
    await db.commit()
    clear_cookies(response)
    return {"ok": True, "message": "Oturum kapatıldı"}


@router.get("/me", summary="Mevcut kimlik bilgilerini getir")
@router.get("/me/", include_in_schema=False)
async def get_me(identity: Dict[str, Any] = Depends(get_current_identity)):
    """
    SIF-01: Identity-aware me endpoint.
    Returns role, type and scoped information.
    """
    return {
        "id": str(identity["id"]),
        "email": identity.get("email"),
        "name": identity.get("name"),
        "role": identity["role"],
        "type": identity["type"],
        # Refine/Frontend uyumluluğu için legacy fields
        "is_admin": identity["role"] == "SOVEREIGN_PRIME",
        "roles": [identity["role"]]
    }
    
@router.post("/identity/keys/generate", summary="Yeni API Anahtarı üret (Sadece PRIME)")
async def generate_identity_key(
    target_id: str, 
    db: "AsyncSession" = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("identity.manage"))
):
    """
    SIF-02: Generates a raw API key for a system identity.
    Returns the key ONLY ONCE.
    """
    import uuid
    svc, _, _, _, _, _ = _svc()
    raw_key = await svc.create_api_key(db, uuid.UUID(target_id), "Default Key")
    return {"id": target_id, "api_key": raw_key, "warning": "Bu anahtarı güvenli bir yere kaydedin, bir daha görüntülenemeyecektir."}

@router.get("/identities", summary="Tüm Sistem Kimliklerini Listele (Sadece PRIME)")
async def list_identities(
    db: "AsyncSession" = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("identity.manage"))
):
    """SIF-02: Lists all system identities for lifecycle management."""
    from sqlalchemy import select
    from libs.db.models.auth_models import SystemIdentity
    res = await db.execute(select(SystemIdentity))
    items = res.scalars().all()
    return [{
        "id": str(i.id), 
        "name": i.name, 
        "is_active": i.is_active,
        "last_used_at": i.last_used_at,
        "risk_level": i.risk_level,
        "trust_score": i.trust_score,
        "quarantined_at": i.quarantined_at
    } for i in items]

@router.post("/identity/{target_id}/quarantine", summary="SIF-04: Ajana Karantina Uygula")
async def quarantine_identity(
    target_id: str,
    db: "AsyncSession" = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("identity.manage"))
):
    """Isolates an agent identity immediately."""
    from sqlalchemy import select
    from libs.db.models.auth_models import SystemIdentity
    import uuid
    from datetime import datetime, timezone
    
    res = await db.execute(select(SystemIdentity).where(SystemIdentity.id == uuid.UUID(target_id)))
    sys_id = res.scalar_one_or_none()
    if not sys_id:
        raise HTTPException(status_code=404, detail="Sistem kimliği bulunamadı.")
        
    sys_id.quarantined_at = datetime.now(timezone.utc)
    sys_id.risk_level = "CRITICAL"
    sys_id.risk_reason = f"Manual Quarantine by {identity['name']}"
    sys_id.trust_score = 0
    
    await db.commit()
    return {"status": "QUARANTINED", "id": target_id}

@router.post("/identity/{target_id}/recover", summary="SIF-04: Ajana Güven Tazele (Recovery)")
async def recover_identity(
    target_id: str,
    db: "AsyncSession" = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("identity.manage"))
):
    """Restores trust and removes quarantine status."""
    from sqlalchemy import select
    from libs.db.models.auth_models import SystemIdentity
    import uuid
    
    res = await db.execute(select(SystemIdentity).where(SystemIdentity.id == uuid.UUID(target_id)))
    sys_id = res.scalar_one_or_none()
    if not sys_id:
        raise HTTPException(status_code=404, detail="Sistem kimliği bulunamadı.")
        
    sys_id.quarantined_at = None
    sys_id.risk_level = "LOW"
    sys_id.trust_score = 100
    sys_id.risk_reason = None
    
    await db.commit()
    return {"status": "RECOVERED", "id": target_id}

@router.get("/health", summary="Auth router health")
@router.get("/health/", include_in_schema=False)
async def auth_router_health():
    return {"ok": True, "status": "SIF-01 ACTIVE"}
