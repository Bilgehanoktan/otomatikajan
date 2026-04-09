"""
Admin Router — Kullanıcı yönetimi ve yetkilendirme (Faz 12)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.routers.auth.jwt_auth import require_admin
from packages.persistence.models import User
from packages.persistence.session import get_db_dep

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", summary="Tüm kullanıcıları listele (Admin Only)")
async def list_users(
    db: AsyncSession = Depends(get_db_dep),
    current_user=Depends(require_admin)
):
    """Sistemdeki tüm kayıtlı kullanıcıları döner."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]

@router.post("/users/{user_id}/toggle-admin", summary="Kullanıcı admin yetkisini değiştir (Admin Only)")
async def toggle_admin(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_dep),
    current_user=Depends(require_admin)
):
    """Belirtilen kullanıcının is_admin flag'ini tersine çevirir."""
    # Kendini adminlikten çıkaramaz (güvenlik)
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Kendi admin yetkinizi kaldıramazsınız.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    user.is_admin = not user.is_admin
    await db.commit()
    
    return {
        "id": str(user.id),
        "email": user.email,
        "is_admin": user.is_admin,
        "message": f"Kullanıcı yetkisi {'admin' if user.is_admin else 'user'} olarak güncellendi."
    }
