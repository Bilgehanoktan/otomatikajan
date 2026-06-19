import pytest
import jwt
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from fastapi import Request
from fastapi.testclient import TestClient

from apps.bilgeapi.config import settings
from apps.bilgeapi.auth import get_current_identity, parse_static_key_hashes
from apps.bilgeapi.adapters.slack_teams import SlackAdapter, TeamsAdapter, SlackMessageFormatter, TeamsMessageFormatter
from apps.bilgeapi.services.release import BilgeAPIReleaseGate

VALID_INCIDENT_PAYLOAD = {
    "project_key": "test-platform",
    "source_system": "backend-api",
    "environment": "production",
    "kind": "backend",
    "severity": "HIGH",
    "error_message": "Connection error",
    "occurred_at": "2026-06-04T13:20:00Z",
    "correlation_id": "req_123"
}

def test_hashed_api_keys_auth(monkeypatch, test_client_real_auth):
    # 1. Setup keys and hashes
    key1 = "secure_admin_key_123456"
    key2 = "secure_operator_key_123456"
    hash1 = hashlib.sha256(key1.encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(key2.encode("utf-8")).hexdigest()
    
    # Clean plaintext keys to ensure only hashes are used for hashed auth
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", [])
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEY_HASHES", [f"{hash1}:admin", f"{hash2}:operator"])
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")

    # 2. Test successful authentication
    headers_admin = {"X-API-Key": key1}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_admin)
    assert resp.status_code == 200

    headers_op = {"X-API-Key": key2}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_op)
    # operator cannot read audit logs (requires audit.read, which operator role doesn't have)
    assert resp.status_code == 403

    # 3. Test invalid key
    headers_invalid = {"X-API-Key": "wrong_key_123"}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_invalid)
    assert resp.status_code == 401


def test_jwt_key_rotation(monkeypatch, test_client_real_auth):
    secret1 = "signing_secret_primary_key_rotation_1"
    secret2 = "old_verification_secret_rotation_2"
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "jwt")
    monkeypatch.setenv("BILGEAPI_JWT_SECRETS", f"{secret1},{secret2}")
    
    # 1. Generate token signed with current primary key (secret1)
    token1 = jwt.encode(
        {"sub": "user123", "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        secret1,
        algorithm="HS256"
    )
    headers_token1 = {"Authorization": f"Bearer {token1}"}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_token1)
    assert resp.status_code == 200

    # 2. Generate token signed with rotated key (secret2)
    token2 = jwt.encode(
        {"sub": "user456", "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        secret2,
        algorithm="HS256"
    )
    headers_token2 = {"Authorization": f"Bearer {token2}"}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_token2)
    assert resp.status_code == 200

    # 3. Generate token signed with unknown key
    token3 = jwt.encode(
        {"sub": "user789", "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "some_random_secret_3",
        algorithm="HS256"
    )
    headers_token3 = {"Authorization": f"Bearer {token3}"}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_token3)
    assert resp.status_code == 401


def test_redis_rate_limiting_fallback(monkeypatch, test_client_real_auth):
    # Set invalid Redis URL to force failure and fallback
    monkeypatch.setattr(settings, "BILGEAPI_REDIS_URL", "redis://invalid_host:9999/0")
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["test_key:admin"])
    monkeypatch.setattr(settings, "BILGEAPI_RATE_LIMIT_RPS", 2)
    
    # Mock redis to fail immediately instead of waiting for a 1-second timeout
    class MockRedis:
        def pipeline(self, *args, **kwargs):
            raise Exception("Simulated immediate connection failure")
    import redis
    monkeypatch.setattr(redis.Redis, "from_url", lambda *args, **kwargs: MockRedis())

    headers = {"X-API-Key": "test_key"}
    
    # Perform requests to trigger rate limiting
    # First request: ok (also clears limit history from previous test runs)
    headers_clear = {**headers, "x-test-clear-limits": "true"}
    resp1 = test_client_real_auth.get("/v1/catalog", headers=headers_clear)
    # Second request: ok
    resp2 = test_client_real_auth.get("/v1/catalog", headers=headers)
    # Third request: 429
    resp3 = test_client_real_auth.get("/v1/catalog", headers=headers)
    
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp3.status_code == 429
    
    # Check that fallback is flagged active
    import apps.bilgeapi.main as bilgeapi_main
    assert bilgeapi_main.REDIS_FALLBACK_ACTIVE is True

    # Check metrics fallback count increment
    if bilgeapi_main.REDIS_FALLBACK_COUNT:
         # Check counter has some value > 0
         from prometheus_client import REGISTRY
         val = REGISTRY.get_sample_value("bilgeapi_redis_fallback_total")
         assert val is not None and val >= 1.0


def test_usage_metering_middleware(monkeypatch, test_client_real_auth):
    secret1 = "signing_secret_primary_key_rotation_1"
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "jwt")
    monkeypatch.setenv("BILGEAPI_JWT_SECRETS", secret1)
    
    # 1. Test JWT claim tenant extraction
    token = jwt.encode(
        {"sub": "user123", "role": "admin", "tenant_id": "tenant-xyz", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        secret1,
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {token}"}
    resp = test_client_real_auth.get("/v1/catalog", headers=headers)
    assert resp.status_code == 200
    
    # Verify prometheus client metric
    from prometheus_client import REGISTRY
    val = REGISTRY.get_sample_value("bilgeapi_tenant_requests_total", {"tenant_id": "tenant-xyz"})
    assert val is not None and val >= 1.0

    # 2. Test X-Tenant-ID header fallback
    headers_tenant = {"Authorization": f"Bearer {token}", "X-Tenant-ID": "custom-tenant"}
    resp = test_client_real_auth.get("/v1/catalog", headers=headers_tenant)
    assert resp.status_code == 200
    
    # Since JWT has tenant_id, it should prioritize JWT claim "tenant-xyz" over header "custom-tenant"
    val = REGISTRY.get_sample_value("bilgeapi_tenant_requests_total", {"tenant_id": "tenant-xyz"})
    assert val is not None


def test_slack_teams_adapters_formatting():
    payload = {
        "incident": {
            "kind": "CRITICAL_DB_LAG",
            "severity": "HIGH",
            "error_message": "DB CPU 100%"
        },
        "diagnostic": {
            "summary": "Database locked",
            "root_cause_hypothesis": "Heavy migration running",
            "confidence": 0.95
        }
    }
    
    # Slack adapter formatting
    slack_fmt = SlackMessageFormatter()
    slack_msg = slack_fmt.format_message("req-123", payload)
    assert "text" in slack_msg
    assert "req-123" in slack_msg["text"]
    assert "CRITICAL_DB_LAG" in slack_msg["text"]
    
    # Teams adapter formatting
    teams_fmt = TeamsMessageFormatter()
    teams_msg = teams_fmt.format_message("req-123", payload)
    assert "text" in teams_msg
    assert "req-123" in teams_msg["text"]
    assert "CRITICAL_DB_LAG" in teams_msg["text"]


@pytest.mark.asyncio
async def test_durable_webhook_queue_dispatch(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_DURABLE_QUEUE_ENABLED", True)
    
    # Import necessary modules
    from libs.queue_abstractions.job_queue import job_queue
    from apps.bilgeapi.services.webhook import WebhookDeliveryService
    from unittest.mock import AsyncMock
    
    # Create mock repos
    webhook_repo = AsyncMock()
    repair_repo = AsyncMock()
    
    delivery_record = {"id": "del-123"}
    webhook_repo.create_delivery.return_value = delivery_record
    
    service = WebhookDeliveryService(
        webhook_repo=webhook_repo,
        repair_repo=repair_repo
    )
    
    payload = {"status": "testing"}
    
    # Stub job_queue.enqueue
    enqueue_mock = AsyncMock()
    monkeypatch.setattr(job_queue, "enqueue", enqueue_mock)
    
    await service.dispatch_webhook(
        repair_request_id="rep-123",
        webhook_url="http://test.url",
        payload=payload
    )
    
    assert enqueue_mock.called
    args = enqueue_mock.call_args[1]
    assert args["delivery_id"] == "del-123"
    assert args["repair_request_id"] == "rep-123"
    assert args["webhook_url"] == "http://test.url"
