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

try:
    from prometheus_client import Gauge
    autonomy_gauge = Gauge(
        "bilgeapi_autonomy_mode_info",
        "Active autonomy mode represented as numeric value (0=OFF, 1=OBSERVE_ONLY, 2=DIAGNOSE_ONLY, 3=SAFE_AUTONOMY, 4=SUPERVISED_AUTONOMY, 5=POLICY_BOUND_AUTONOMY)",
        ["mode"]
    )
    system_health_gauge = Gauge(
        "bilgeapi_system_health_status",
        "System health status (1=OK/HEALTHY, 0=DEGRADED/ERROR)"
    )
except Exception:
    autonomy_gauge = None
    system_health_gauge = None

AUTONOMY_MODE_MAP = {
    "OFF": 0,
    "OBSERVE_ONLY": 1,
    "DIAGNOSE_ONLY": 2,
    "SAFE_AUTONOMY": 3,
    "SUPERVISED_AUTONOMY": 4,
    "POLICY_BOUND_AUTONOMY": 5
}

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
    if autonomy_gauge:
        try:
            mode = settings.BILGEAPI_AUTONOMY_MODE
            val = AUTONOMY_MODE_MAP.get(mode, 1)
            autonomy_gauge.labels(mode=mode).set(val)
        except Exception as exc:
            logger.warning(f"Failed to set autonomy metric: {exc}")

    if system_health_gauge:
        try:
            skill_status = getattr(request.app.state, "skill_registry_status", "UNKNOWN")
            system_health_gauge.set(1.0 if skill_status == "HEALTHY" else 0.0)
        except Exception as exc:
            logger.warning(f"Failed to set system health metric: {exc}")

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
