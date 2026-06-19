"""
tests/unit/bilgeapi/test_observability.py — Phase 10
Tests for observability features: health, metrics, correlation ID,
path sanitization, security headers, and graceful shutdown.
"""
import asyncio
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ══════════════════════════════════════════════════════════════════════════════
# Path Sanitization Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestPathSanitization:
    def test_uuid_replaced(self):
        from apps.bilgeapi.main import sanitize_path
        path = "/v1/repair-requests/a1b2c3d4-e5f6-7890-abcd-ef1234567890/dispatch"
        result = sanitize_path(path)
        assert "{uuid}" in result
        assert "a1b2c3d4" not in result

    def test_hex_id_replaced(self):
        from apps.bilgeapi.main import sanitize_path
        path = "/v1/incidents/abcdef12345678"
        result = sanitize_path(path)
        assert "{id}" in result
        assert "abcdef12345678" not in result

    def test_static_path_unchanged(self):
        from apps.bilgeapi.main import sanitize_path
        path = "/v1/catalog"
        assert sanitize_path(path) == "/v1/catalog"

    def test_health_path_unchanged(self):
        from apps.bilgeapi.main import sanitize_path
        assert sanitize_path("/health") == "/health"

    def test_multiple_uuids(self):
        from apps.bilgeapi.main import sanitize_path
        path = "/v1/a1b2c3d4-e5f6-7890-abcd-ef1234567890/sub/b2c3d4e5-f6a7-8901-bcde-f12345678901"
        result = sanitize_path(path)
        assert result.count("{uuid}") == 2


# ══════════════════════════════════════════════════════════════════════════════
# Public /health Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestPublicHealth:
    def test_health_returns_ok(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "bilgeapi"
        assert "version" in data
        assert "auth_mode" in data

    def test_health_does_not_expose_internals(self, test_client):
        """Public /health should NOT expose memory, db pool, or otel details."""
        response = test_client.get("/health")
        data = response.json()
        assert "memory" not in data
        assert "db" not in data
        assert "otel" not in data
        assert "background_tasks" not in data


# ══════════════════════════════════════════════════════════════════════════════
# Admin /v1/ops/health Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestDetailedHealth:
    def test_ops_health_returns_detailed_info(self, test_client):
        """With auth disabled, /v1/ops/health returns detailed system info."""
        response = test_client.get("/v1/ops/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "memory" in data
        assert "rss_mb" in data["memory"]
        assert "db" in data
        assert "otel" in data
        assert "background_tasks" in data
        assert "timestamp" in data

    def test_ops_health_memory_has_rss(self, test_client):
        response = test_client.get("/v1/ops/health")
        data = response.json()
        mem = data["memory"]
        assert "rss_mb" in mem
        assert "status" in mem
        # rss_mb should be a number (or None if psutil fails)
        if mem["rss_mb"] is not None:
            assert isinstance(mem["rss_mb"], (int, float))

    def test_ops_health_otel_info(self, test_client):
        response = test_client.get("/v1/ops/health")
        data = response.json()
        otel = data["otel"]
        assert "enabled" in otel
        assert "available" in otel


# ══════════════════════════════════════════════════════════════════════════════
# /metrics Endpoint Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestMetricsEndpoint:
    def test_metrics_returns_200(self, test_client):
        response = test_client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, test_client):
        response = test_client.get("/metrics")
        content_type = response.headers.get("content-type", "")
        # Should be text/plain or text/plain; version=0.0.4; charset=utf-8
        assert "text/plain" in content_type or "text/" in content_type

    def test_metrics_contains_prometheus_format(self, test_client):
        """Metrics output should contain at least one metric family."""
        response = test_client.get("/metrics")
        text = response.text
        # prometheus_client always includes process and python info collectors
        assert "# HELP" in text or "# TYPE" in text or "python_" in text or "process_" in text

    def test_metrics_production_guard(self, test_client):
        """When APP_ENV=production and BILGEAPI_METRICS_PUBLIC=false, /metrics requires auth."""
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_METRICS_PUBLIC"] = "false"
        try:
            response = test_client.get("/metrics")
            assert response.status_code == 401
        finally:
            os.environ["APP_ENV"] = "development"
            os.environ.pop("BILGEAPI_METRICS_PUBLIC", None)


# ══════════════════════════════════════════════════════════════════════════════
# X-Correlation-ID Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestCorrelationID:
    def test_correlation_id_generated_if_missing(self, test_client):
        response = test_client.get("/health")
        corr_id = response.headers.get("X-Correlation-ID")
        assert corr_id is not None
        assert len(corr_id) > 0

    def test_correlation_id_preserved_if_provided(self, test_client):
        custom_id = "my-custom-trace-12345"
        response = test_client.get("/health", headers={"X-Correlation-ID": custom_id})
        assert response.headers.get("X-Correlation-ID") == custom_id

    def test_correlation_id_on_api_routes(self, test_client):
        response = test_client.get("/v1/catalog")
        assert "X-Correlation-ID" in response.headers


# ══════════════════════════════════════════════════════════════════════════════
# Security Headers Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurityHeaders:
    def test_health_has_nosniff(self, test_client):
        """/health should have X-Content-Type-Options: nosniff."""
        response = test_client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_metrics_has_nosniff(self, test_client):
        """/metrics should have X-Content-Type-Options: nosniff."""
        response = test_client.get("/metrics")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_health_no_strict_csp(self, test_client):
        """/health should NOT have strict CSP (sandbox) applied."""
        response = test_client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "sandbox" not in csp

    def test_api_route_has_full_csp(self, test_client):
        """API routes should have full CSP headers."""
        response = test_client.get("/v1/catalog")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "sandbox" in csp

    def test_docs_no_csp(self, test_client):
        """/docs path should not have CSP applied (Swagger UI needs inline scripts)."""
        response = test_client.get("/docs")
        # Docs might redirect but shouldn't have sandbox CSP
        csp = response.headers.get("Content-Security-Policy", "")
        assert "sandbox" not in csp


# ══════════════════════════════════════════════════════════════════════════════
# Rate Limiter Bypass Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestRateLimiterBypass:
    def test_health_bypasses_rate_limit(self, test_client):
        """Even with high request volume, /health should always respond 200."""
        for _ in range(20):
            r = test_client.get("/health")
            assert r.status_code == 200

    def test_metrics_bypasses_rate_limit(self, test_client):
        """Even with high request volume, /metrics should always respond 200."""
        for _ in range(20):
            r = test_client.get("/metrics")
            assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# Background Task Tracking Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestBackgroundTaskTracking:
    def test_background_tasks_set_exists(self):
        from apps.bilgeapi.services.webhook import background_tasks
        assert isinstance(background_tasks, set)

    def test_track_task_adds_and_removes(self):
        from apps.bilgeapi.services.webhook import background_tasks, _track_task

        async def _dummy():
            pass

        loop = asyncio.new_event_loop()
        try:
            async def _test():
                task = asyncio.create_task(_dummy())
                _track_task(task)
                assert task in background_tasks
                await task
                # After completion, done_callback should have discarded the task
                # Give callback a chance to execute
                await asyncio.sleep(0)
                assert task not in background_tasks

            loop.run_until_complete(_test())
        finally:
            loop.close()


# ══════════════════════════════════════════════════════════════════════════════
# Graceful Shutdown Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestGracefulShutdown:
    def test_shutdown_timeout_config(self):
        from apps.bilgeapi.config import settings
        # Default value should be 5.0
        assert settings.BILGEAPI_SHUTDOWN_TIMEOUT_S == 5.0

    def test_shutdown_timeout_configurable(self):
        from apps.bilgeapi.config import settings
        os.environ["BILGEAPI_SHUTDOWN_TIMEOUT_S"] = "10.0"
        try:
            assert settings.BILGEAPI_SHUTDOWN_TIMEOUT_S == 10.0
        finally:
            os.environ["BILGEAPI_SHUTDOWN_TIMEOUT_S"] = "5.0"


# ══════════════════════════════════════════════════════════════════════════════
# Prometheus Counter Integration Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestPrometheusCounters:
    def test_counters_registered(self):
        """Verify that our custom Prometheus counters are importable and exist."""
        from apps.bilgeapi.main import (
            REQUEST_COUNT, REQUEST_DURATION,
            WEBHOOK_DELIVERIES, WEBHOOK_DEAD_LETTERS,
            REPAIR_REQUESTS, RELEASE_GATE_SCORE,
            BACKGROUND_TASKS_PENDING,
            _PROMETHEUS_AVAILABLE,
        )
        assert _PROMETHEUS_AVAILABLE is True
        assert REQUEST_COUNT is not None
        assert REQUEST_DURATION is not None
        assert WEBHOOK_DELIVERIES is not None
        assert WEBHOOK_DEAD_LETTERS is not None
        assert REPAIR_REQUESTS is not None
        assert RELEASE_GATE_SCORE is not None
        assert BACKGROUND_TASKS_PENDING is not None

    def test_metrics_endpoint_includes_custom_metrics(self, test_client):
        """After making an API request, /metrics should contain bilgeapi metrics."""
        # Make a request to trigger the metrics middleware
        test_client.get("/v1/catalog")
        response = test_client.get("/metrics")
        text = response.text
        assert "bilgeapi_http_requests_total" in text


# ══════════════════════════════════════════════════════════════════════════════
# Config Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestObservabilityConfig:
    def test_metrics_public_default(self):
        from apps.bilgeapi.config import settings
        os.environ.pop("BILGEAPI_METRICS_PUBLIC", None)
        assert settings.BILGEAPI_METRICS_PUBLIC is True

    def test_metrics_public_false(self):
        from apps.bilgeapi.config import settings
        os.environ["BILGEAPI_METRICS_PUBLIC"] = "false"
        try:
            assert settings.BILGEAPI_METRICS_PUBLIC is False
        finally:
            os.environ.pop("BILGEAPI_METRICS_PUBLIC", None)
