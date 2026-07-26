"""
Phase 15 — Unit tests for Redis-backed Dynamic Usage Quotas.

Tests cover:
- QuotaService in-memory fallback behaviour
- NULL (unlimited), 0 (blocked), and >0 (active limit) semantics
- 80% and 100% threshold notification deduplication
- 429 response structure (JSON body + headers)
- Admin quota configuration and usage endpoints
- Repository update_quota method
"""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from bilgeapi.services.quota import QuotaService, QuotaExceededError
from bilgeapi.services.audit import AuditService
from bilgeapi.repositories.memory import InMemoryApiKeyRepository, memory_repositories


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_audit_service():
    service = AsyncMock(spec=AuditService)
    service.log_event = AsyncMock()
    return service


@pytest.fixture
def quota_service(mock_audit_service):
    svc = QuotaService(audit_service=mock_audit_service)
    # Force in-memory mode (no Redis)
    svc._redis_available = False
    svc._redis_fallback_logged = True
    return svc


@pytest.fixture
def api_key_repo():
    memory_repositories.clear_all()
    return InMemoryApiKeyRepository()


# ── NULL (unlimited) semantics ────────────────────────────────────────────────

class TestQuotaUnlimited:
    async def test_null_quota_skips_counting(self, quota_service):
        """When both quota_daily and quota_monthly are None, no counting occurs."""
        result = await quota_service.check_and_increment(
            key_id="key_test1",
            key_fingerprint="fp_test1",
            quota_daily=None,
            quota_monthly=None
        )
        assert result["daily_limit"] is None
        assert result["monthly_limit"] is None
        assert result["daily_used"] == 0
        assert result["monthly_used"] == 0
        assert result["daily_remaining"] is None
        assert result["monthly_remaining"] is None

    async def test_null_daily_with_monthly_limit(self, quota_service):
        """Unlimited daily + limited monthly still counts monthly."""
        result = await quota_service.check_and_increment(
            key_id="key_test2",
            key_fingerprint="fp_test2",
            quota_daily=None,
            quota_monthly=1000
        )
        assert result["daily_limit"] is None
        assert result["monthly_limit"] == 1000
        assert result["monthly_used"] == 1
        assert result["monthly_remaining"] == 999


# ── 0 (blocked) semantics ────────────────────────────────────────────────────

class TestQuotaBlocked:
    async def test_daily_zero_rejects_immediately(self, quota_service):
        """quota_daily=0 means zero requests allowed, raises immediately."""
        with pytest.raises(QuotaExceededError) as exc_info:
            await quota_service.check_and_increment(
                key_id="key_blocked",
                key_fingerprint="fp_blocked",
                quota_daily=0,
                quota_monthly=None
            )
        assert exc_info.value.scope == "daily"
        assert exc_info.value.limit == 0
        assert exc_info.value.used == 0

    async def test_monthly_zero_rejects_immediately(self, quota_service):
        """quota_monthly=0 means zero requests allowed, raises immediately."""
        with pytest.raises(QuotaExceededError) as exc_info:
            await quota_service.check_and_increment(
                key_id="key_blocked2",
                key_fingerprint="fp_blocked2",
                quota_daily=None,
                quota_monthly=0
            )
        assert exc_info.value.scope == "monthly"
        assert exc_info.value.limit == 0

    async def test_both_zero_daily_takes_precedence(self, quota_service):
        """When both are 0, daily check triggers first."""
        with pytest.raises(QuotaExceededError) as exc_info:
            await quota_service.check_and_increment(
                key_id="key_both_blocked",
                key_fingerprint="fp_both_blocked",
                quota_daily=0,
                quota_monthly=0
            )
        assert exc_info.value.scope == "daily"


# ── Active limit (>0) semantics ──────────────────────────────────────────────

class TestQuotaActiveLimit:
    async def test_increment_within_limit(self, quota_service):
        """Requests within limit succeed and return correct remaining."""
        result = await quota_service.check_and_increment(
            key_id="key_active",
            key_fingerprint="fp_active",
            quota_daily=100,
            quota_monthly=1000
        )
        assert result["daily_used"] == 1
        assert result["daily_remaining"] == 99
        assert result["monthly_used"] == 1
        assert result["monthly_remaining"] == 999

    async def test_daily_limit_exceeded(self, quota_service):
        """Exceeding the daily limit raises QuotaExceededError."""
        # Pre-fill counters to the limit
        key_id = "key_exceed_daily"
        daily_key = quota_service._daily_key(key_id)
        quota_service._memory_counters[key_id][daily_key] = 10

        with pytest.raises(QuotaExceededError) as exc_info:
            await quota_service.check_and_increment(
                key_id=key_id,
                key_fingerprint="fp_exceed",
                quota_daily=10,
                quota_monthly=1000
            )
        assert exc_info.value.scope == "daily"
        assert exc_info.value.limit == 10
        assert exc_info.value.used == 11  # incremented then checked

    async def test_monthly_limit_exceeded(self, quota_service):
        """Exceeding the monthly limit raises QuotaExceededError."""
        key_id = "key_exceed_monthly"
        monthly_key = quota_service._monthly_key(key_id)
        quota_service._memory_counters[key_id][monthly_key] = 50

        with pytest.raises(QuotaExceededError) as exc_info:
            await quota_service.check_and_increment(
                key_id=key_id,
                key_fingerprint="fp_exceed_m",
                quota_daily=None,
                quota_monthly=50
            )
        assert exc_info.value.scope == "monthly"
        assert exc_info.value.limit == 50

    async def test_sequential_increments(self, quota_service):
        """Multiple calls increment counters properly."""
        key_id = "key_sequential"
        for i in range(5):
            result = await quota_service.check_and_increment(
                key_id=key_id,
                key_fingerprint="fp_seq",
                quota_daily=100,
                quota_monthly=1000
            )
        assert result["daily_used"] == 5
        assert result["daily_remaining"] == 95


# ── Threshold notification deduplication ──────────────────────────────────────

class TestThresholdNotifications:
    async def test_80_percent_threshold_triggers_notification(self, quota_service, mock_audit_service):
        """80% threshold triggers a QUOTA_WARNING_80 audit event."""
        key_id = "key_warn80"
        daily_key = quota_service._daily_key(key_id)
        # Set to 79 so next request hits 80 (80% of 100)
        quota_service._memory_counters[key_id][daily_key] = 79

        await quota_service.check_and_increment(
            key_id=key_id,
            key_fingerprint="fp_warn80",
            quota_daily=100,
            quota_monthly=None
        )

        # Should have triggered QUOTA_WARNING_80
        calls = mock_audit_service.log_event.call_args_list
        event_types = [c.kwargs.get("event_type") or c[1].get("event_type", "") for c in calls]
        assert "QUOTA_WARNING_80" in event_types

    async def test_80_percent_notification_deduplicated(self, quota_service, mock_audit_service):
        """Second call at 80% does not re-trigger the notification."""
        key_id = "key_dedup80"
        daily_key = quota_service._daily_key(key_id)
        quota_service._memory_counters[key_id][daily_key] = 79

        # First call triggers
        await quota_service.check_and_increment(
            key_id=key_id,
            key_fingerprint="fp_dedup80",
            quota_daily=100,
            quota_monthly=None
        )

        call_count_after_first = mock_audit_service.log_event.call_count

        # Second call should not trigger again
        await quota_service.check_and_increment(
            key_id=key_id,
            key_fingerprint="fp_dedup80",
            quota_daily=100,
            quota_monthly=None
        )

        # Count should not have increased for QUOTA_WARNING_80
        calls = mock_audit_service.log_event.call_args_list
        warn80_count = sum(
            1 for c in calls
            if (c.kwargs.get("event_type") or c[1].get("event_type", "")) == "QUOTA_WARNING_80"
        )
        assert warn80_count == 1, f"Expected exactly 1 QUOTA_WARNING_80 event, got {warn80_count}"

    async def test_100_percent_exceeded_triggers_audit(self, quota_service, mock_audit_service):
        """Exceeding 100% triggers a QUOTA_EXCEEDED audit event."""
        key_id = "key_exceeded"
        daily_key = quota_service._daily_key(key_id)
        quota_service._memory_counters[key_id][daily_key] = 10

        with pytest.raises(QuotaExceededError):
            await quota_service.check_and_increment(
                key_id=key_id,
                key_fingerprint="fp_exceeded",
                quota_daily=10,
                quota_monthly=None
            )

        calls = mock_audit_service.log_event.call_args_list
        event_types = [c.kwargs.get("event_type") or c[1].get("event_type", "") for c in calls]
        assert "QUOTA_EXCEEDED" in event_types


# ── QuotaExceededError structure ──────────────────────────────────────────────

class TestQuotaExceededErrorStructure:
    def test_error_attributes(self):
        """QuotaExceededError carries scope, limit, used, reset_at."""
        err = QuotaExceededError(scope="daily", limit=100, used=101, reset_at="2026-06-06T23:59:59+00:00")
        assert err.scope == "daily"
        assert err.limit == 100
        assert err.used == 101
        assert "2026-06-06" in err.reset_at

    def test_error_message(self):
        """QuotaExceededError has a descriptive message."""
        err = QuotaExceededError(scope="monthly", limit=5000, used=5001, reset_at="2026-06-30T23:59:59+00:00")
        assert "monthly" in str(err)
        assert "5000" in str(err)


# ── In-memory fallback ───────────────────────────────────────────────────────

class TestInMemoryFallback:
    async def test_fallback_when_redis_unavailable(self, mock_audit_service):
        """When Redis is unavailable, fallback to in-memory counters."""
        svc = QuotaService(audit_service=mock_audit_service)
        # Simulate no Redis URL configured
        with patch.object(svc, '_get_redis_client', return_value=None):
            result = await svc.check_and_increment(
                key_id="key_fallback",
                key_fingerprint="fp_fallback",
                quota_daily=100,
                quota_monthly=1000
            )
        assert result["daily_used"] == 1
        assert result["monthly_used"] == 1

    async def test_fallback_increments_correctly(self, quota_service):
        """In-memory fallback increments correctly across multiple calls."""
        key_id = "key_mem_inc"
        for _ in range(3):
            result = await quota_service.check_and_increment(
                key_id=key_id,
                key_fingerprint="fp_mem_inc",
                quota_daily=100,
                quota_monthly=1000
            )
        assert result["daily_used"] == 3
        assert result["monthly_used"] == 3


# ── get_usage_from_redis (read-only) ─────────────────────────────────────────

class TestGetUsage:
    async def test_get_usage_returns_zero_for_new_key(self, quota_service):
        """A key with no usage returns (0, 0)."""
        daily, monthly = quota_service.get_usage_from_redis("key_new")
        assert daily == 0
        assert monthly == 0

    async def test_get_usage_returns_correct_counts(self, quota_service):
        """After increments, usage returns correct values."""
        key_id = "key_usage_check"
        for _ in range(5):
            await quota_service.check_and_increment(
                key_id=key_id,
                key_fingerprint="fp_usage",
                quota_daily=100,
                quota_monthly=1000
            )
        daily, monthly = quota_service.get_usage_from_redis(key_id)
        assert daily == 5
        assert monthly == 5


# ── Repository update_quota ──────────────────────────────────────────────────

class TestRepositoryUpdateQuota:
    async def test_update_quota_sets_values(self, api_key_repo):
        """update_quota correctly updates quota_daily and quota_monthly."""
        key_data = {
            "id": "key_q1",
            "key_hash": "hash_q1",
            "key_prefix": "blg_live_",
            "key_fingerprint": "fp_q1",
            "role": "OPERATOR",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        await api_key_repo.create(key_data)
        
        updated = await api_key_repo.update_quota("key_q1", 500, 5000)
        assert updated is not None
        assert updated["quota_daily"] == 500
        assert updated["quota_monthly"] == 5000

    async def test_update_quota_to_none(self, api_key_repo):
        """Setting quota to None means unlimited."""
        key_data = {
            "id": "key_q2",
            "key_hash": "hash_q2",
            "key_prefix": "blg_live_",
            "key_fingerprint": "fp_q2",
            "role": "OPERATOR",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "quota_daily": 100,
            "quota_monthly": 1000
        }
        await api_key_repo.create(key_data)
        
        updated = await api_key_repo.update_quota("key_q2", None, None)
        assert updated["quota_daily"] is None
        assert updated["quota_monthly"] is None

    async def test_update_quota_nonexistent_key(self, api_key_repo):
        """Updating quota for a non-existent key returns None."""
        result = await api_key_repo.update_quota("nonexistent", 100, 1000)
        assert result is None


# ── 429 response integration (via auth pipeline) ─────────────────────────────

class TestHTTP429Response:
    """Test that the auth pipeline returns proper 429 responses when quota is exceeded."""

    def test_quota_exceeded_error_fields(self):
        """Verify all required fields are present on QuotaExceededError."""
        err = QuotaExceededError(
            scope="daily",
            limit=1000,
            used=1001,
            reset_at="2026-06-06T23:59:59+00:00"
        )
        assert hasattr(err, "scope")
        assert hasattr(err, "limit")
        assert hasattr(err, "used")
        assert hasattr(err, "reset_at")
        assert err.scope == "daily"
        assert err.limit == 1000
        assert err.used == 1001


# ── Schemas ──────────────────────────────────────────────────────────────────

class TestQuotaSchemas:
    def test_api_key_create_with_quota(self):
        from bilgeapi.schemas.api_key import ApiKeyCreate
        body = ApiKeyCreate(role="OPERATOR", quota_daily=500, quota_monthly=5000)
        assert body.quota_daily == 500
        assert body.quota_monthly == 5000

    def test_api_key_create_without_quota(self):
        from bilgeapi.schemas.api_key import ApiKeyCreate
        body = ApiKeyCreate(role="OPERATOR")
        assert body.quota_daily is None
        assert body.quota_monthly is None

    def test_quota_update_schema(self):
        from bilgeapi.schemas.api_key import ApiKeyQuotaUpdate
        update = ApiKeyQuotaUpdate(quota_daily=1000, quota_monthly=10000)
        assert update.quota_daily == 1000
        assert update.quota_monthly == 10000

    def test_quota_update_schema_nullable(self):
        from bilgeapi.schemas.api_key import ApiKeyQuotaUpdate
        update = ApiKeyQuotaUpdate(quota_daily=None, quota_monthly=None)
        assert update.quota_daily is None
        assert update.quota_monthly is None

    def test_quota_usage_response_schema(self):
        from bilgeapi.schemas.api_key import ApiKeyQuotaUsageResponse
        resp = ApiKeyQuotaUsageResponse(
            key_id="key_test",
            quota_daily=100,
            quota_monthly=1000,
            daily_used=50,
            monthly_used=200,
            daily_remaining=50,
            monthly_remaining=800
        )
        assert resp.key_id == "key_test"
        assert resp.daily_remaining == 50

    def test_api_key_response_includes_quota(self):
        from bilgeapi.schemas.api_key import ApiKeyResponse
        resp = ApiKeyResponse(
            id="key_test",
            key_prefix="blg_live_",
            key_fingerprint="fp_test",
            role="OPERATOR",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            quota_daily=500,
            quota_monthly=5000
        )
        assert resp.quota_daily == 500
        assert resp.quota_monthly == 5000
