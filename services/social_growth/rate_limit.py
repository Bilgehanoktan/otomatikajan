"""Redis-backed fixed-window ingress limiter for Meta webhooks."""

from __future__ import annotations

import time
from typing import Protocol

DEFAULT_REQUESTS_PER_MINUTE = 120


class RateLimitRedisClient(Protocol):
    """Subset of redis-py used by the webhook limiter."""

    def incr(self, name: str) -> int:
        """Increment and return a bucket counter."""

    def expire(self, name: str, ttl_seconds: int) -> object:
        """Set the bucket expiry."""


class RedisWebhookRateLimiter:
    """Limit requests per client address with short-lived Redis buckets."""

    def __init__(
        self,
        client: RateLimitRedisClient,
        *,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        key_prefix: str = "social-growth:webhook-rate:",
    ) -> None:
        if requests_per_minute < 1:
            raise ValueError("requests_per_minute pozitif olmalı")
        self._client = client
        self._requests_per_minute = requests_per_minute
        self._key_prefix = key_prefix

    def allow(self, client_key: str) -> bool:
        """Atomically count the current minute and reject over-limit callers."""

        bucket = int(time.time() // 60)
        redis_key = f"{self._key_prefix}{client_key}:{bucket}"
        count = self._client.incr(redis_key)
        if count == 1:
            self._client.expire(redis_key, 70)
        return count <= self._requests_per_minute
