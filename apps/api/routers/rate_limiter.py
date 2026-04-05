"""
Rate Limiter — Faz 2
• Sliding window algoritması
• IP bazlı + kullanıcı bazlı limitler
• Redis varsa Redis'te, yoksa in-memory fallback
• FastAPI Depends ile kolay entegrasyon
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field


# ── Limit Tanımları ───────────────────────────────────────
@dataclass
class RateLimit:
    requests: int    # izin verilen istek sayısı
    window_s: float  # zaman penceresi (saniye)
    label:    str    # açıklama


# Varsayılan limitler
LIMITS = {
    "global":           RateLimit(200, 60,  "200 istek/dk (IP başına)"),
    "projects_create":  RateLimit(10,  60,  "10 proje/dk"),
    "auth_login":       RateLimit(5,   60,  "5 giriş denemesi/dk"),
    "auth_register":    RateLimit(3,   300, "3 kayıt/5dk"),
    "heal_manual":      RateLimit(20,  60,  "20 heal sorgusu/dk"),
}


# ════════════════════════════════════════════════════════
# In-Memory Sliding Window (Redis yoksa)
# ════════════════════════════════════════════════════════
class InMemoryRateLimiter:
    """
    Her (key, bucket) çifti için timestamp listesi tutar.
    Pencere dışına çıkanları atar, pencere içindekileri sayar.
    """

    def __init__(self):
        # key -> deque of timestamps
        self._windows: dict[str, deque] = defaultdict(lambda: deque())

    def check(self, key: str, limit: RateLimit) -> tuple[bool, int, float]:
        """
        Returns:
            allowed:    İstek geçti mi
            remaining:  Kalan istek hakkı
            reset_in:   Pencerenin sıfırlanmasına kaç saniye
        """
        now  = time.time()
        dq   = self._windows[key]
        cutoff = now - limit.window_s

        # Eski kayıtları temizle
        while dq and dq[0] < cutoff:
            dq.popleft()

        count = len(dq)
        if count >= limit.requests:
            oldest    = dq[0] if dq else now
            reset_in  = float(max(0.0, oldest + limit.window_s - now))
            return False, 0, reset_in

        dq.append(now)
        remaining = limit.requests - count - 1
        reset_in  = float(limit.window_s)
        return True, remaining, reset_in

    def reset(self, key: str) -> float:
        """Key'i sıfırla ve sıfırlama zamanını float olarak döndür (RC1 compat)."""
        self._windows.pop(key, None)
        return float(0.0)


_limiter = InMemoryRateLimiter()


# ════════════════════════════════════════════════════════
# FastAPI Dependency Factories
# ════════════════════════════════════════════════════════
def _get_client_ip(request) -> str:
    """X-Forwarded-For varsa ilk IP'yi al (reverse proxy arkasında)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── FastAPI entegrasyonu (lazy import) ───────────────────
def rate_limit(bucket: str = "global"):
    limit = LIMITS.get(bucket, LIMITS["global"])
    async def _check(request):
        from fastapi import HTTPException, status
        ip  = _get_client_ip(request)
        key = f"{bucket}:{ip}"
        allowed, remaining, reset_in = _limiter.check(key, limit)
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset     = int(reset_in)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={"error": "Çok fazla istek", "limit": limit.label,
                        "reset_in": f"{reset_in:.1f}sn"},
                headers={"Retry-After": str(int(reset_in)),
                         "X-RateLimit-Limit": str(limit.requests),
                         "X-RateLimit-Remaining": "0",
                         "X-RateLimit-Reset": str(int(time.time() + reset_in))},
            )
    return _check

# ── Response Header Middleware ────────────────────────────
try:
    from starlette.middleware.base import BaseHTTPMiddleware as _Base
    class RateLimitHeaderMiddleware(_Base):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            rem = getattr(request.state, "rate_limit_remaining", None)
            rst = getattr(request.state, "rate_limit_reset", None)
            if rem is not None:
                response.headers["X-RateLimit-Remaining"] = str(rem)
            if rst is not None:
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + rst)
            return response
except ImportError:
    class RateLimitHeaderMiddleware:  # type: ignore
        pass


# ════════════════════════════════════════════════════════
# Redis Sliding Window Rate Limiter (çok-worker desteği)
# ════════════════════════════════════════════════════════
class RedisRateLimiter:
    """
    Redis Lua script ile atomik sliding window.
    Birden fazla Uvicorn/Gunicorn worker arasında paylaşılır.
    Redis yoksa InMemoryRateLimiter'a otomatik fallback.
    """

    _SCRIPT = """
local key    = KEYS[1]
local now    = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit  = tonumber(ARGV[3])
local cutoff = now - window

redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
local count = redis.call('ZCARD', key)
if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local reset  = (oldest[2] or now) + window - now
    return {0, 0, math.ceil(reset)}
end
redis.call('ZADD', key, now, now .. '-' .. math.random(1e9))
redis.call('EXPIRE', key, math.ceil(window) + 1)
local remaining = limit - count - 1
return {1, remaining, math.ceil(window)}
"""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._client    = None
        self._script_sha: str | None = None

    async def _get_client(self):
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(
                    self._redis_url, decode_responses=True, socket_timeout=1.0
                )
                self._script_sha = await self._client.script_load(self._SCRIPT)
            except Exception:
                self._client = None
        return self._client

    async def check_async(
        self, key: str, limit: RateLimit
    ) -> tuple[bool, int, float]:
        """Async Redis check — çağrılamıyorsa InMemory fallback."""
        client = await self._get_client()
        if not client:
            return _limiter.check(key, limit)

        import time as _time
        try:
            now = _time.time()
            result = await client.evalsha(
                self._script_sha,
                1, key,
                now, limit.window_s, limit.requests,
            )
            allowed, remaining, reset_in = int(result[0]), int(result[1]), float(result[2])
            return bool(allowed), remaining, reset_in
        except Exception:
            # Redis geçici arıza -> in-memory fallback
            return _limiter.check(key, limit)


def _build_redis_limiter() -> RedisRateLimiter | None:
    """REDIS_URL varsa Redis limiter oluştur, yoksa None."""
    import os
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return None
    return RedisRateLimiter(redis_url)


_redis_limiter: RedisRateLimiter | None = _build_redis_limiter()


# ── Birleşik check fonksiyonu ─────────────────────────────
async def check_rate_limit(key: str, limit: RateLimit) -> tuple[bool, int, float]:
    """
    Redis varsa Redis'te, yoksa in-memory sliding window.
    Tüm API katmanları bu fonksiyonu kullanır.
    """
    if _redis_limiter:
        return await _redis_limiter.check_async(key, limit)
    return _limiter.check(key, limit)


def rate_limit_async(bucket: str = "global"):
    """
    Redis-aware async FastAPI Depends factory.
    Eski rate_limit() fonksiyonunun üretim kaliteli versiyonu.
    """
    limit = LIMITS.get(bucket, LIMITS["global"])

    async def _check(request):
        from fastapi import HTTPException, Request
        ip  = _get_client_ip(request)
        key = f"{bucket}:{ip}"
        allowed, remaining, reset_in = await check_rate_limit(key, limit)
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset     = int(reset_in)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error":    "Çok fazla istek",
                    "limit":    limit.label,
                    "reset_in": f"{reset_in:.1f}sn",
                    "backend":  "redis" if _redis_limiter else "memory",
                },
                headers={
                    "Retry-After":          str(int(reset_in)),
                    "X-RateLimit-Limit":    str(limit.requests),
                    "X-RateLimit-Remaining":"0",
                    "X-RateLimit-Reset":    str(int(time.time() + reset_in)),
                },
            )

    return _check
