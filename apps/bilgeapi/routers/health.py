from fastapi import APIRouter
from apps.bilgeapi.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "bilgeapi",
        "version": "1.0.0",
        "auth_mode": settings.BILGEAPI_AUTH_MODE
    }
