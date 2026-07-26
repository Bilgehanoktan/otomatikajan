"""
apps/bilgeapi/routers/metrics.py - Phase 10
Prometheus-compatible /metrics endpoint for BilgeAPI.
"""
import hashlib
import hmac
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select

from apps.bilgeapi.config import settings
from apps.bilgeapi.models.database import ApiKeyModel

logger = logging.getLogger("bilgeapi.metrics")

router = APIRouter()


def _has_admin_static_hash(api_key: str) -> bool:
    from apps.bilgeapi.auth import parse_static_key_hashes

    api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    for configured_hash, role in parse_static_key_hashes().items():
        if hmac.compare_digest(api_key_hash, configured_hash):
            return role in ("ADMIN", "SOVEREIGN_PRIME")
    return False


async def _has_admin_db_key(api_key: str) -> bool:
    from libs.db.session import AsyncSessionLocal

    api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ApiKeyModel).where(
                ApiKeyModel.key_hash == api_key_hash,
                ApiKeyModel.is_active.is_(True),
            )
        )
        api_key_row = result.scalar_one_or_none()

    if not api_key_row:
        return False

    expires_at = api_key_row.expires_at
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            return False

    return api_key_row.role.upper() in ("ADMIN", "SOVEREIGN_PRIME")


async def _metrics_guard(request: Request):
    """
    In production, /metrics requires admin auth unless BILGEAPI_METRICS_PUBLIC=true.
    In dev/test, /metrics is always public.
    """
    if settings.APP_ENV == "production" and not settings.BILGEAPI_METRICS_PUBLIC:
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="Metrics endpoint requires authentication in production")

        if _has_admin_static_hash(api_key):
            return

        try:
            if await _has_admin_db_key(api_key):
                return
        except Exception as exc:
            logger.warning(f"Failed to validate /metrics DB API key: {exc}")

        raise HTTPException(status_code=403, detail="Metrics endpoint requires admin privileges")


@router.get("/metrics", tags=["Observability"], response_class=PlainTextResponse)
async def prometheus_metrics(request: Request):
    """Expose Prometheus-format metrics for scraping."""
    await _metrics_guard(request)
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return PlainTextResponse(
            content=generate_latest().decode("utf-8"),
            media_type=CONTENT_TYPE_LATEST,
        )
    except ImportError:
        logger.warning("prometheus_client not installed, /metrics returning empty")
        return PlainTextResponse(
            content="# prometheus_client not available\n",
            media_type="text/plain",
        )
