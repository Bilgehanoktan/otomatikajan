import pytest
import hmac
import hashlib
import time
from datetime import datetime, timezone, timedelta
from apps.bilgeapi.config import settings

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

def test_api_key_lifecycle_and_rbac(monkeypatch, test_client_real_auth):
    # Enable API Key Auth Mode with dynamic keys
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    # Also set a static key for admin operations to create dynamic keys
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_static_key:admin", "op_static_key:operator"])
    
    headers_admin = {"X-API-Key": "admin_static_key"}
    headers_op = {"X-API-Key": "op_static_key"}
    
    # 1. Non-admin (OPERATOR) tries to create a dynamic key -> 403 Forbidden
    resp = test_client_real_auth.post("/v1/admin/api-keys", json={
        "role": "OPERATOR",
        "description": "Test Operator Key"
    }, headers=headers_op)
    assert resp.status_code == 403

    # 2. Admin successfully creates a dynamic key
    resp = test_client_real_auth.post("/v1/admin/api-keys", json={
        "role": "OPERATOR",
        "description": "Test Operator Key",
        "tenant_id": "tenant-alpha"
    }, headers=headers_admin)
    assert resp.status_code == 201
    created_data = resp.json()
    
    # Plaintext key should be present in creation response
    assert "plaintext_key" in created_data
    assert created_data["plaintext_key"].startswith("blg_live_")
    plaintext_key = created_data["plaintext_key"]
    key_id = created_data["id"]
    assert created_data["role"] == "OPERATOR"
    assert created_data["description"] == "Test Operator Key"
    assert created_data["tenant_id"] == "tenant-alpha"
    assert created_data["is_active"] is True

    # 3. List keys as Admin -> Plaintext key and key_hash should NOT be leaked
    resp = test_client_real_auth.get("/v1/admin/api-keys", headers=headers_admin)
    assert resp.status_code == 200
    keys_list = resp.json()
    assert len(keys_list) >= 1
    
    found_key = None
    for k in keys_list:
        if k["id"] == key_id:
            found_key = k
            break
    assert found_key is not None
    assert "plaintext_key" not in found_key
    assert "key_hash" not in found_key
    assert found_key["key_fingerprint"] == created_data["key_fingerprint"]
    assert found_key["tenant_id"] == "tenant-alpha"

    # 4. Detail key as Admin -> Plaintext key and key_hash should NOT be leaked
    resp = test_client_real_auth.get(f"/v1/admin/api-keys/{key_id}", headers=headers_admin)
    assert resp.status_code == 200
    detail_key = resp.json()
    assert "plaintext_key" not in detail_key
    assert "key_hash" not in detail_key
    assert detail_key["key_fingerprint"] == created_data["key_fingerprint"]
    assert detail_key["tenant_id"] == "tenant-alpha"

    # 5. Use the newly created dynamic key to make an authorized request (create incident)
    headers_dynamic = {"X-API-Key": plaintext_key}
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_dynamic)
    assert resp.status_code == 201

    # 6. Revoke the key as Admin
    resp = test_client_real_auth.post(f"/v1/admin/api-keys/{key_id}/revoke", json={
        "reason": "Security rotation"
    }, headers=headers_admin)
    assert resp.status_code == 200
    revoked_data = resp.json()
    assert revoked_data["is_active"] is False
    assert revoked_data["revoked_by"].startswith("api_key_")
    assert "admin_static_key" not in revoked_data["revoked_by"]
    assert revoked_data["revoke_reason"] == "Security rotation"
    assert revoked_data["revoked_at"] is not None

    # 7. Try to use the revoked key -> 401 Unauthorized
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_dynamic)
    assert resp.status_code == 401

def test_api_key_expiration(monkeypatch, test_client_real_auth):
    # Enable API Key Auth Mode with dynamic keys
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_static_key:admin"])
    headers_admin = {"X-API-Key": "admin_static_key"}

    # 1. Create a key that expires in 1 day
    resp = test_client_real_auth.post("/v1/admin/api-keys", json={
        "role": "OPERATOR",
        "description": "Short-lived Key",
        "expires_in_days": 1
    }, headers=headers_admin)
    assert resp.status_code == 201
    key_data = resp.json()
    assert key_data["expires_at"] is not None

    # Use it -> works
    headers_dynamic = {"X-API-Key": key_data["plaintext_key"]}
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_dynamic)
    assert resp.status_code == 201

    # 2. Mock memory/db repository to set expires_at in the past
    from apps.bilgeapi.repositories.memory import memory_repositories
    key_id = key_data["id"]
    memory_repositories.api_keys[key_id]["expires_at"] = datetime.now(timezone.utc) - timedelta(hours=1)

    # Try to use it -> 401 Unauthorized
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_dynamic)
    assert resp.status_code == 401

def test_api_key_fallbacks(monkeypatch, test_client_real_auth):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEY_HASHES", [
        f"{hashlib.sha256(b'hashed_op_key').hexdigest()}:operator"
    ])
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["plaintext_op_key:operator"])

    # 1. When APP_ENV is development
    monkeypatch.setenv("APP_ENV", "development")

    # DB key works (if existed)
    # Hashed static key works
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers={"X-API-Key": "hashed_op_key"})
    assert resp.status_code == 201

    # Plaintext static key works
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers={"X-API-Key": "plaintext_op_key"})
    assert resp.status_code == 201

    # 2. When APP_ENV is production
    monkeypatch.setenv("APP_ENV", "production")

    # Hashed static key works
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers={"X-API-Key": "hashed_op_key"})
    assert resp.status_code == 201

    # Plaintext static key MUST NOT work in production -> 401
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers={"X-API-Key": "plaintext_op_key"})
    assert resp.status_code == 401

def test_api_key_last_used_throttling(monkeypatch, test_client_real_auth):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_static_key:admin"])
    headers_admin = {"X-API-Key": "admin_static_key"}

    resp = test_client_real_auth.post("/v1/admin/api-keys", json={
        "role": "OPERATOR"
    }, headers=headers_admin)
    key_data = resp.json()
    plaintext_key = key_data["plaintext_key"]
    key_id = key_data["id"]

    headers_dynamic = {"X-API-Key": plaintext_key}

    # 1. First usage -> updates last_used_at
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_dynamic)
    assert resp.status_code == 201
    
    from apps.bilgeapi.repositories.memory import memory_repositories
    # Fetch from repository
    key_in_db = memory_repositories.api_keys[key_id]
    first_used_at = key_in_db.get("last_used_at")
    assert first_used_at is not None

    # 2. Second usage immediately -> should NOT update last_used_at (throttled)
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_dynamic)
    assert resp.status_code == 201
    
    second_used_at = memory_repositories.api_keys[key_id].get("last_used_at")
    assert second_used_at == first_used_at

    # 3. Mock first used time to be 70 seconds ago
    memory_repositories.api_keys[key_id]["last_used_at"] = datetime.now(timezone.utc) - timedelta(seconds=70)
    mocked_time = memory_repositories.api_keys[key_id]["last_used_at"]

    # Third usage -> should update last_used_at
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_dynamic)
    assert resp.status_code == 201
    
    # Wait briefly for async task to write
    time.sleep(0.05)
    third_used_at = memory_repositories.api_keys[key_id].get("last_used_at")
    assert third_used_at != mocked_time
    assert third_used_at > mocked_time

def test_api_key_audit_redaction(monkeypatch, test_client_real_auth):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_static_key:admin"])
    headers_admin = {"X-API-Key": "admin_static_key"}

    # Create dynamic key
    resp = test_client_real_auth.post("/v1/admin/api-keys", json={
        "role": "OPERATOR",
        "description": "audit-check-key"
    }, headers=headers_admin)
    key_data = resp.json()
    plaintext_key = key_data["plaintext_key"]

    # Use dynamic key
    test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers={"X-API-Key": plaintext_key})

    # Retrieve audit events
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_admin)
    assert resp.status_code == 200
    events = resp.json()

    # Verify that no event contains the plaintext key or key hash, but they do contain fingerprint/prefix
    for event in events:
        event_str = str(event)
        # Check plaintext_key is redacted / not present
        assert plaintext_key not in event_str
        # If there is key creation or usage event, check details
        metadata = event.get("metadata") or {}
        # The word 'key' is automatically redacted in AuditService,
        # but our specific metadata key 'fingerprint' should be preserved!
        if event["event_type"] == "API_KEY_CREATED":
            assert metadata.get("fingerprint") == key_data["key_fingerprint"]
            assert metadata.get("prefix") == key_data["key_prefix"]
            assert "key_hash" not in metadata
        elif event["event_type"] == "API_KEY_USED":
            assert metadata.get("fingerprint") == key_data["key_fingerprint"]
            assert metadata.get("role") == "OPERATOR"
