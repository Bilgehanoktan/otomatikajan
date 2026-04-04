"""
JWT Auth — Faz 3 + Güvenlik Revizyonu
• Access (15dk) + Refresh (7gün) token çifti
• bcrypt parola hash
• Token rotasyonu — eski refresh geçersiz
• Revocation: iptal edilen refresh token'lar DB'de işaretlenir
• JWT_SECRET tek kaynaktan okunur (config modülü)
• OWASP: secret min 64 karakter, rastgele üretilmeli
"""

import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Any, Optional, Union, TYPE_CHECKING

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie

# bcrypt lazy import — import-time crash önler; kurulu değilse hashlib.pbkdf2 fallback
try:
    import bcrypt as _bcrypt
    _BCRYPT_OK = True
except ImportError:
    _bcrypt = None  # type: ignore
    _BCRYPT_OK = False
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db_dep
from db.models import User, RefreshToken

# ─── JWT Konfigürasyonu — TEK KAYNAK ─────────────────────
from config import JWT_SECRET
JWT_ALGORITHM = "HS256"

# Geliştirme modunda uyarı ver, üretimde hard fail (main.py'de kontrol edilir)
if not JWT_SECRET:
    JWT_SECRET = secrets.token_hex(64)   # Her yeniden başlatmada yeni — dev only!
    print(
        "UYARI: JWT_SECRET ayarlanmamış. "
        "Her yeniden başlatmada oturum invalidate olur. "
        "Üretim için JWT_SECRET env değişkenini ayarlayın (min 64 karakter)."
    )
    if os.getenv("APP_ENV") == "production":
        raise RuntimeError("CRITICAL: APP_ENV=production ama JWT_SECRET ayarlanmamış! Sistem güvenli başlatılamaz.")
elif len(JWT_SECRET) < 64:
    print(
        f"UYARI: JWT_SECRET çok kısa ({len(JWT_SECRET)} karakter). "
        "OWASP en iyi uygulamalarına göre min 64 karakter gereklidir. "
        "Örnek üretim: python -c \"import secrets; print(secrets.token_hex(64))\""
    )
    if os.getenv("APP_ENV") == "production":
        raise RuntimeError("CRITICAL: JWT_SECRET production için 64 karakterden kısa olamaz!")

ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_MINUTES", "15"))
REFRESH_DAYS   = int(os.getenv("JWT_REFRESH_DAYS", "7"))

router  = APIRouter()
_bearer = HTTPBearer(auto_error=False)


# ── Pydantic Modelleri ─────────────────────────────────────
class RegisterRequest(BaseModel):
    email:    str
    password: str

class LoginRequest(BaseModel):
    email:    str
    password: str

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    is_admin:      bool = False
    token_type:    str = "bearer"
    expires_in:    int = ACCESS_MINUTES * 60   # saniye cinsinden
    roles:         list[str] = []


# ── Token Üretimi / Doğrulama ─────────────────────────────
def _make_token(payload: dict, expires_delta: timedelta) -> str:
    data = {**payload, "exp": datetime.now(timezone.utc) + expires_delta,
            "iat": datetime.now(timezone.utc)}
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi doldu")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")


# ── Cookie Yardımcıları ───────────────────────────────────
def set_auth_cookies(response: Response, access_token: str, refresh_token: str, request: Request = None):
    """httpOnly cookie'leri ayarlar. Local / HTTP uyumluluğu için secure flag'i smart kontrol edilir."""
    from config import APP_ENV
    
    # SRE Hardening: localhost veya 127.0.0.1 ise secure=False (HTTPS zorunluluğunu kaldır)
    is_secure = APP_ENV == "production"
    if request:
        host = request.url.hostname or ""
        if host in ("localhost", "127.0.0.1", "0.0.0.0"):
            is_secure = False
        elif request.url.scheme == "http":
            is_secure = False

    # Access Token (15 dk)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_MINUTES * 60,
        expires=ACCESS_MINUTES * 60,
        samesite="lax",
        secure=is_secure,
    )
    # Refresh Token (7 gün)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_DAYS * 24 * 3600,
        expires=REFRESH_DAYS * 24 * 3600,
        samesite="lax",
        secure=is_secure,
    )

def clear_auth_cookies(response: Response):
    """Cookie'leri temizler."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


# ── Auth Service ──────────────────────────────────────────
class AuthService:

    async def register(self, db: AsyncSession, email: str, password: str) -> "User":
        from db.models import User
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı")

        # Parola politikası
        if len(password) < 8:
            raise HTTPException(status_code=422, detail="Parola en az 8 karakter olmalıdır")

        if not _BCRYPT_OK or _bcrypt is None:
            if os.getenv("APP_ENV") == "production":
                raise RuntimeError("CRITICAL: bcrypt paketi production ortamında zorunludur!")
            raise RuntimeError("bcrypt kurulu değil: pip install bcrypt")
        
        # Analyzer guard
        assert _bcrypt is not None
        hashed = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt(rounds=12)).decode()
        user = User(email=email, hashed_password=hashed)
        db.add(user)
        await db.flush()
        return user

    async def login(self, db: AsyncSession, email: str, password: str) -> TokenResponse:
        from db.models import User, RefreshToken
        result = await db.execute(select(User).where(User.email == email))
        user   = result.scalar_one_or_none()

        # Zamanlama saldırısını önle — her zaman hash kontrol et
        if not user:
            (_BCRYPT_OK and _bcrypt is not None) and _bcrypt.checkpw(b"dummy", _bcrypt.hashpw(b"dummy", _bcrypt.gensalt()))
            raise HTTPException(status_code=401, detail="Hatalı e-posta veya parola")

        if not _BCRYPT_OK or _bcrypt is None or not _bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
            raise HTTPException(status_code=401, detail="Hatalı e-posta veya parola")
        
        assert _bcrypt is not None

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Hesap devre dışı")

        access  = _make_token({
            "sub": str(user.id),
            "email": user.email,
            "type": "access",
            "roles": ["admin"] if user.is_admin else ["user"]
        }, timedelta(minutes=ACCESS_MINUTES))
        refresh = _make_token({"sub": str(user.id), "type": "refresh"},
                               timedelta(days=REFRESH_DAYS))

        rt = RefreshToken(
            user_id=user.id,
            token=refresh,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS),
            revoked=False,
        )
        db.add(rt)
        roles = ["admin"] if user.is_admin else ["user"]
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            is_admin=user.is_admin,
            roles=roles
        )

    async def refresh(self, db: AsyncSession, refresh_token: str) -> TokenResponse:
        """
        Token rotasyonu:
        1. Refresh token'ı doğrula
        2. DB'de revoked=False olduğunu kontrol et
        3. Eski token'ı iptal et (revocation)
        4. Yeni çift üret
        """
        # from db.models import User, RefreshToken # Removed, now top-level
        from sqlalchemy import update

        payload = _decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Geçersiz token tipi")

        # DB'de geçerli mi kontrol et (revocation)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token  == refresh_token,
                RefreshToken.revoked == False,       # noqa: E712
            )
        )
        rt = result.scalar_one_or_none()
        if not rt:
            raise HTTPException(
                status_code=401,
                detail="Refresh token bulunamadı, süresi dolmuş veya iptal edilmiş",
            )

        # Token rotasyonu: eski token'ı iptal et
        rt.revoked = True
        await db.flush()

        # Kullanıcıyı al ve yeni çift üret
        user_res = await db.execute(select(User).where(User.id == rt.user_id))
        user = user_res.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı veya devre dışı")

        access  = _make_token({
            "sub": str(user.id),
            "email": user.email,
            "type": "access",
            "roles": ["admin"] if user.is_admin else ["user"]
        }, timedelta(minutes=ACCESS_MINUTES))
        new_refresh = _make_token({"sub": str(user.id), "type": "refresh"},
                                   timedelta(days=REFRESH_DAYS))

        new_rt = RefreshToken(
            user_id=user.id,
            token=new_refresh,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS),
            revoked=False,
        )
        db.add(new_rt)
        roles = ["admin"] if user.is_admin else ["user"]
        return TokenResponse(
            access_token=access,
            refresh_token=new_refresh,
            is_admin=user.is_admin,
            roles=roles
        )

    async def revoke_all(self, db: AsyncSession, user_id: str) -> int:
        """Kullanıcının tüm aktif refresh token'larını iptal eder (logout all)."""
        from db.models import RefreshToken
        from sqlalchemy import update
        result = await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)  # noqa
            .values(revoked=True)
        )
        return result.rowcount

    async def get_user_from_token(self, db: AsyncSession, token: str) -> Any:
        from db.models import User
        payload = _decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Access token gerekli")
        result = await db.execute(select(User).where(User.id == payload["sub"]))
        user   = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı veya devre dışı")
        return user


auth_service = AuthService()


# ── FastAPI Depends ────────────────────────────────────────
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_dep),
):
    """
    Kullanıcıyı doğrular.
    Faz 12.1 Resilience: 
    - JWT Hataları (401): Sessiz fallback / Redirect.
    - DB Hataları: 500 at (Refresh döngüsü oluşmaması için).
    """
    from sqlalchemy.exc import SQLAlchemyError
    
    header_token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        header_token = auth_header.split(" ")[1]
        try:
            return await auth_service.get_user_from_token(db, header_token)
        except SQLAlchemyError as se:
            logger.error(f"[AUTH-RESILIENCE] DB Hatası (Header): {se}")
            raise HTTPException(status_code=500, detail="Kimlik doğrulama sunucusu meşgul (DB).")
        except Exception:
            pass
    
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        try:
            return await auth_service.get_user_from_token(db, cookie_token)
        except SQLAlchemyError as se:
            logger.error(f"[AUTH-RESILIENCE] DB Hatası (Cookie): {se}")
            raise HTTPException(status_code=500, detail="Kimlik doğrulama sunucusu meşgul (DB).")
        except Exception:
            pass
            
    raise HTTPException(status_code=401, detail="Oturum geçersiz veya yetkilendirme gerekli")


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db_dep),
):
    """Token varsa kullanıcıyı döndür, yoksa None döndür (dev mode)."""
    if not credentials:
        return None
    try:
        return await auth_service.get_user_from_token(db, credentials.credentials)
    except Exception:
        return None


async def require_admin(user=Depends(get_current_user)):
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    return user


async def optional_admin(user=Depends(get_optional_user)):
    """Dev modunda veya kullanıcı admin ise izin ver."""
    env = os.getenv("APP_ENV", "development")
    if env == "development":
        return user
    if not user or not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    return user


# ── Endpoint'ler ──────────────────────────────────────────
@router.post("/register", response_model=dict, summary="Yeni kullanıcı kaydı")
async def register(req: RegisterRequest, response: Response, request: Request, db: AsyncSession = Depends(get_db_dep)):
    user = await auth_service.register(db, req.email, req.password)
    # Kayıt sonrası otomatik login — UX iyileştirmesi
    res = await auth_service.login(db, req.email, req.password)
    set_auth_cookies(response, res.access_token, res.refresh_token, request=request)
    return {"id": str(user.id), "email": user.email, "created": True, "token": res.access_token}


@router.post("/login", response_model=TokenResponse, summary="Giriş — token al")
async def login(req: LoginRequest, response: Response, request: Request, db: AsyncSession = Depends(get_db_dep)):
    res = await auth_service.login(db, req.email, req.password)
    set_auth_cookies(response, res.access_token, res.refresh_token, request=request)
    return res


@router.post("/refresh", response_model=TokenResponse, summary="Token rotasyonu")
async def refresh_token(
    request: Request,
    response: Response,
    body: Optional[dict] = None,
    db: AsyncSession = Depends(get_db_dep)
):
    # 1. Öncelik: Body
    rt = (body or {}).get("refresh_token", "")
    
    # 2. İkincil: Cookie Fallback (Silent Refresh)
    if not rt:
        rt = request.cookies.get("refresh_token", "")
        
    if not rt:
        raise HTTPException(status_code=422, detail="refresh_token gerekli")
    
    res = await auth_service.refresh(db, rt)
    # Yeni token'ları cookie olarak da set et (Önemli: Rotasyon)
    set_auth_cookies(response, res.access_token, res.refresh_token, request=request)
    return res


@router.post("/logout", summary="Tüm oturumları kapat")
async def logout_all(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_dep),
):
    count = await auth_service.revoke_all(db, str(user.id))
    return {"revoked_sessions": count}
