"""
QuotaService — Redis-backed dynamic usage quota enforcement.

Provides daily and monthly request counting per API key with:
- Atomic Redis pipeline increments
- Graceful in-memory fallback on Redis failure
- Deduplicated %80 and %100 threshold notifications
- Standardized 429 responses with X-RateLimit-* headers
"""
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple

from apps.bilgeapi.config import settings
from apps.bilgeapi.services.audit import AuditService

logger = logging.getLogger("bilgeapi.quota")


class QuotaExceededError(Exception):
    """Raised when an API key exceeds its quota."""
    def __init__(self, scope: str, limit: int, used: int, reset_at: str):
        self.scope = scope
        self.limit = limit
        self.used = used
        self.reset_at = reset_at
        super().__init__(f"Quota exceeded: {scope} limit={limit}, used={used}")


class QuotaService:
    """
    Redis-backed quota enforcement service with in-memory fallback.
    
    Key semantics for quota_daily / quota_monthly:
      - None  → unlimited (no quota enforcement)
      - 0     → blocked (zero requests allowed)
      - >0    → active limit
    """

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service
        self._redis_client = None
        self._redis_available = True
        self._redis_fallback_logged = False
        # In-memory fallback counters: {key_id: {date_key: count}}
        self._memory_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # In-memory marker keys for notification deduplication
        self._memory_markers: Dict[str, bool] = {}

    def _get_redis_client(self):
        """Lazily initialize and return the Redis client."""
        if not settings.BILGEAPI_REDIS_URL:
            return None
        if self._redis_client is None:
            try:
                import redis
                self._redis_client = redis.Redis.from_url(
                    settings.BILGEAPI_REDIS_URL,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0,
                    decode_responses=True
                )
                # Test connectivity
                self._redis_client.ping()
                self._redis_available = True
                self._redis_fallback_logged = False
            except Exception as e:
                logger.error(f"Failed to initialize Redis client for quota: {e}")
                self._redis_client = None
                self._redis_available = False
        return self._redis_client

    def _daily_key(self, key_id: str) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"quota:{key_id}:daily:{date_str}"

    def _monthly_key(self, key_id: str) -> str:
        month_str = datetime.now(timezone.utc).strftime("%Y-%m")
        return f"quota:{key_id}:monthly:{month_str}"

    def _daily_reset_at(self) -> str:
        """ISO timestamp of end of current UTC day."""
        now = datetime.now(timezone.utc)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
        return end_of_day.isoformat()

    def _monthly_reset_at(self) -> str:
        """ISO timestamp of end of current UTC month."""
        now = datetime.now(timezone.utc)
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        return end_of_month.isoformat()

    def _increment_redis(self, key_id: str) -> Tuple[int, int]:
        """
        Atomically increment daily and monthly counters in Redis using a pipeline.
        Returns (daily_count, monthly_count).
        Raises on Redis failure.
        """
        client = self._get_redis_client()
        if not client:
            raise ConnectionError("Redis not available")

        daily_key = self._daily_key(key_id)
        monthly_key = self._monthly_key(key_id)

        pipe = client.pipeline()
        pipe.incr(daily_key)
        pipe.expire(daily_key, 36 * 3600)  # TTL: 36 hours
        pipe.incr(monthly_key)
        pipe.expire(monthly_key, 35 * 24 * 3600)  # TTL: 35 days
        results = pipe.execute()

        daily_count = int(results[0])
        monthly_count = int(results[2])
        return daily_count, monthly_count

    def _increment_memory(self, key_id: str) -> Tuple[int, int]:
        """Fallback in-memory counter increment."""
        daily_key = self._daily_key(key_id)
        monthly_key = self._monthly_key(key_id)
        self._memory_counters[key_id][daily_key] += 1
        self._memory_counters[key_id][monthly_key] += 1
        return (
            self._memory_counters[key_id][daily_key],
            self._memory_counters[key_id][monthly_key]
        )

    def _check_marker(self, marker_key: str) -> bool:
        """Check if a notification marker exists (deduplicate). Returns True if already sent."""
        client = self._get_redis_client()
        if client and self._redis_available:
            try:
                return bool(client.exists(marker_key))
            except Exception:
                pass
        # Fallback to memory
        return self._memory_markers.get(marker_key, False)

    def _set_marker(self, marker_key: str, ttl_seconds: int = 36 * 3600):
        """Set a notification marker to prevent duplicate notifications."""
        client = self._get_redis_client()
        if client and self._redis_available:
            try:
                client.setex(marker_key, ttl_seconds, "1")
                return
            except Exception:
                pass
        # Fallback to memory
        self._memory_markers[marker_key] = True

    async def _send_threshold_notification(
        self,
        key_id: str,
        key_fingerprint: str,
        scope: str,
        threshold_pct: int,
        limit: int,
        used: int
    ):
        """Send a deduplicated threshold notification via audit and webhook."""
        now = datetime.now(timezone.utc)
        if scope == "daily":
            period_key = now.strftime("%Y-%m-%d")
        else:
            period_key = now.strftime("%Y-%m")

        marker_key = f"quota:{key_id}:{scope}:{period_key}:warn{threshold_pct}_sent"

        if self._check_marker(marker_key):
            return  # Already sent

        self._set_marker(marker_key)

        event_type = f"QUOTA_WARNING_{threshold_pct}" if threshold_pct < 100 else "QUOTA_EXCEEDED"

        await self.audit_service.log_event(
            event_type=event_type,
            actor_id=key_id,
            actor_type="system",
            entity_type="api_key",
            entity_id=key_id,
            metadata={
                "fingerprint": key_fingerprint,
                "scope": scope,
                "threshold_pct": threshold_pct,
                "limit": limit,
                "used": used,
                "period": period_key
            }
        )

        logger.warning(
            f"Quota {event_type}: key={key_fingerprint} scope={scope} "
            f"limit={limit} used={used} ({threshold_pct}%)"
        )

    def get_usage_from_redis(self, key_id: str) -> Tuple[int, int]:
        """Get current daily and monthly usage from Redis (read-only)."""
        client = self._get_redis_client()
        if client and self._redis_available:
            try:
                daily_key = self._daily_key(key_id)
                monthly_key = self._monthly_key(key_id)
                pipe = client.pipeline()
                pipe.get(daily_key)
                pipe.get(monthly_key)
                results = pipe.execute()
                daily_count = int(results[0] or 0)
                monthly_count = int(results[1] or 0)
                return daily_count, monthly_count
            except Exception:
                pass

        # Fallback to memory
        daily_key = self._daily_key(key_id)
        monthly_key = self._monthly_key(key_id)
        return (
            self._memory_counters.get(key_id, {}).get(daily_key, 0),
            self._memory_counters.get(key_id, {}).get(monthly_key, 0)
        )

    async def check_and_increment(
        self,
        key_id: str,
        key_fingerprint: str,
        quota_daily: Optional[int],
        quota_monthly: Optional[int]
    ) -> Dict[str, Any]:
        """
        Check quota limits and increment usage counter.
        
        Returns a dict with quota headers info:
          {
            "daily_limit": ..., "daily_used": ..., "daily_remaining": ...,
            "monthly_limit": ..., "monthly_used": ..., "monthly_remaining": ...,
          }
        
        Raises QuotaExceededError if limit is exceeded.
        """
        # Handle quota=0 (blocked) — reject immediately without counting
        if quota_daily is not None and quota_daily == 0:
            raise QuotaExceededError(
                scope="daily",
                limit=0,
                used=0,
                reset_at=self._daily_reset_at()
            )
        if quota_monthly is not None and quota_monthly == 0:
            raise QuotaExceededError(
                scope="monthly",
                limit=0,
                used=0,
                reset_at=self._monthly_reset_at()
            )

        # Both unlimited — skip counting entirely
        if quota_daily is None and quota_monthly is None:
            return {
                "daily_limit": None, "daily_used": 0, "daily_remaining": None,
                "monthly_limit": None, "monthly_used": 0, "monthly_remaining": None
            }

        # Increment counters
        use_redis = True
        try:
            daily_count, monthly_count = self._increment_redis(key_id)
            if not self._redis_available:
                self._redis_available = True
                self._redis_fallback_logged = False
                logger.info("Redis connection recovered for quota service")
        except Exception as e:
            use_redis = False
            daily_count, monthly_count = self._increment_memory(key_id)
            if not self._redis_fallback_logged:
                self._redis_fallback_logged = True
                self._redis_available = False
                logger.warning(
                    f"Redis unavailable for quota, using in-memory fallback: {e}"
                )

        # Check daily limit
        if quota_daily is not None and daily_count > quota_daily:
            await self._send_threshold_notification(
                key_id, key_fingerprint, "daily", 100, quota_daily, daily_count
            )
            raise QuotaExceededError(
                scope="daily",
                limit=quota_daily,
                used=daily_count,
                reset_at=self._daily_reset_at()
            )

        # Check monthly limit
        if quota_monthly is not None and monthly_count > quota_monthly:
            await self._send_threshold_notification(
                key_id, key_fingerprint, "monthly", 100, quota_monthly, monthly_count
            )
            raise QuotaExceededError(
                scope="monthly",
                limit=quota_monthly,
                used=monthly_count,
                reset_at=self._monthly_reset_at()
            )

        # Check 80% threshold for daily
        if quota_daily is not None and daily_count >= int(quota_daily * 0.8) and daily_count <= quota_daily:
            await self._send_threshold_notification(
                key_id, key_fingerprint, "daily", 80, quota_daily, daily_count
            )

        # Check 80% threshold for monthly
        if quota_monthly is not None and monthly_count >= int(quota_monthly * 0.8) and monthly_count <= quota_monthly:
            await self._send_threshold_notification(
                key_id, key_fingerprint, "monthly", 80, quota_monthly, monthly_count
            )

        # Build response
        daily_remaining = (quota_daily - daily_count) if quota_daily is not None else None
        monthly_remaining = (quota_monthly - monthly_count) if quota_monthly is not None else None

        return {
            "daily_limit": quota_daily,
            "daily_used": daily_count,
            "daily_remaining": max(0, daily_remaining) if daily_remaining is not None else None,
            "monthly_limit": quota_monthly,
            "monthly_used": monthly_count,
            "monthly_remaining": max(0, monthly_remaining) if monthly_remaining is not None else None
        }


# Singleton instance (lazy-initialized per request via dependency injection)
_quota_service_instance: Optional[QuotaService] = None


def get_quota_service_instance(audit_service: AuditService) -> QuotaService:
    """Get or create a module-level QuotaService singleton."""
    global _quota_service_instance
    if _quota_service_instance is None:
        _quota_service_instance = QuotaService(audit_service)
    return _quota_service_instance
