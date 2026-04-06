"""
Auth Router — /api/v1/auth prefix ile kayıtlı
Faz 8'deki lazy facade yaklaşımının Faz 12'ye geri alınmış hali.
"""

from typing import TYPE_CHECKING
from fastapi import APIRouter, Depends, Response, Request, HTTPException, status

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from packages.persistence.session import get_db_dep
from apps.api.routers.apps.api.routers.auth.jwt_auth import get_current_user

router = APIRouter()


def _svc():
    """
    Lazy import:
    - circular import riskini düşürür
    - import-time patlamaları azaltır
    """
    from apps.api.routers.apps.api.routers.auth.jwt_auth import (
        auth_service,
        RegisterRequest,
        LoginRequest,
        TokenResponse,
        set_auth_cookies,
        clear_auth_cookies,
    )
    return auth_service, RegisterRequest, LoginRequest, TokenResponse, set_auth_cookies, clear_auth_cookies


@router.post("/register", summary="Yeni kullanıcı kaydı")
async def register(body: dict, db: "AsyncSession" = Depends(get_db_dep)):
    svc, Reg, _, _, _, _ = _svc()
    user = await svc.register(db, body["email"], body["password"])
    return {"id": str(user.id), "email": user.email}


@router.post("/login", summary="Giriş — token al")
async def login(response: Response, request: Request, body: dict, db: "AsyncSession" = Depends(get_db_dep)):
    svc, _, _, _, set_cookies, _ = _svc()
    res = await svc.login(db, body["email"], body["password"])
    set_cookies(response, res.access_token, res.refresh_token, request=request)
    return res


@router.post("/refresh", summary="Access token yenile")
async def refresh(request: Request, response: Response, body: dict | None = None, db: "AsyncSession" = Depends(get_db_dep)):
    svc, _, _, _, set_cookies, _ = _svc()
    rt = (body or {}).get("refresh_token")
    
    # Body'de yoksa cookie'den bak
    if not rt:
        rt = request.cookies.get("refresh_token")
        
    if not rt:
        raise HTTPException(status_code=422, detail="refresh_token gerekli (body veya cookie)")
        
    res = await svc.refresh(db, rt)
    set_cookies(response, res.access_token, res.refresh_token, request=request)
    return res


@router.post("/logout", summary="Oturumu kapat")
async def logout(response: Response, current_user=Depends(get_current_user), db: "AsyncSession" = Depends(get_db_dep)):
    svc, _, _, _, _, clear_cookies = _svc()
    await svc.revoke_all(db, str(current_user.id))
    clear_cookies(response)
    return {"ok": True, "message": "Oturum kapatıldı"}


@router.get("/me", summary="Mevcut kullanıcı bilgilerini getir")
async def get_me(current_user=Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "roles": ["admin"] if current_user.is_admin else ["user"]
    }

@router.get("/health", summary="Auth router health")
async def auth_router_health():
    return {"ok": True, "router": "apps.api.routers.auth.router"}
