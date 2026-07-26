import pytest
import time
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
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

# test_client_real_auth is now defined in conftest.py

def test_static_keys_rbac(monkeypatch, test_client_real_auth):
    # Enable API Key Auth Mode with role suffix mapping
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator", "obs_key:audit_observer", "default_key"])
    
    # 1. ADMIN key: should access read audits (requires bilgeapi.audit.read) and create incident (incident.write)
    headers_admin = {"X-API-Key": "admin_key"}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_admin)
    assert resp.status_code == 200
    
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_admin)
    assert resp.status_code == 201
    
    # 2. OPERATOR key: should create incident but fail to view audit events (403)
    headers_op = {"X-API-Key": "op_key"}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_op)
    assert resp.status_code == 403
    assert "SIF-03 ACCESS DENIED" in resp.json()["detail"]
    
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_op)
    assert resp.status_code == 201
    
    # 3. AUDIT_OBSERVER key: should view audit events but fail to create incident (403)
    headers_obs = {"X-API-Key": "obs_key"}
    resp = test_client_real_auth.get("/v1/audit-events", headers=headers_obs)
    assert resp.status_code == 200
    
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_obs)
    assert resp.status_code == 403
    
    # 4. Default key (no role specified): should get default role OPERATOR
    headers_def = {"X-API-Key": "default_key"}
    resp = test_client_real_auth.post("/v1/incidents", json=VALID_INCIDENT_PAYLOAD, headers=headers_def)
    assert resp.status_code == 201

def test_jwt_rbac(monkeypatch, test_client_real_auth):
    # Enable JWT Auth Mode
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "jwt")
    monkeypatch.setattr(settings, "BILGEAPI_JWT_SECRET", "test_jwt_signing_secret_123")
    
    # 1. Invalid JWT token
    headers_bad = {"Authorization": "Bearer bad_token_content"}
    resp = test_client_real_auth.get("/v1/catalog", headers=headers_bad)
    assert resp.status_code == 401
    
    # 2. Expired JWT token
    expired_token = jwt.encode({
        "sub": "some_user",
        "role": "operator",
        "exp": int((datetime.now(timezone.utc) - timedelta(seconds=10)).timestamp())
    }, "test_jwt_signing_secret_123", algorithm="HS256")
    headers_exp = {"Authorization": f"Bearer {expired_token}"}
    resp = test_client_real_auth.get("/v1/catalog", headers=headers_exp)
    assert resp.status_code == 401
    assert "doldu" in resp.json()["detail"] or "expired" in resp.json()["detail"].lower()
    
    # 3. Valid Operator JWT
    op_token = jwt.encode({
        "sub": "user_op_1",
        "role": "operator",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
    }, "test_jwt_signing_secret_123", algorithm="HS256")
    headers_op = {"Authorization": f"Bearer {op_token}"}
    resp = test_client_real_auth.get("/v1/catalog", headers=headers_op)
    assert resp.status_code == 200

def test_rate_limiting(monkeypatch, test_client_real_auth):
    # Enable JWT and set RPS limit to 2
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "jwt")
    monkeypatch.setattr(settings, "BILGEAPI_JWT_SECRET", "secret")
    monkeypatch.setattr(settings, "BILGEAPI_RATE_LIMIT_RPS", 2)
    
    token = jwt.encode({
        "sub": "user",
        "role": "admin",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
    }, "secret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Clear rate limit and first request -> 200
    headers_clear = {**headers, "X-Test-Clear-Limits": "true"}
    resp1 = test_client_real_auth.get("/v1/catalog", headers=headers_clear)
    assert resp1.status_code == 200
    
    # Second request -> 200
    resp2 = test_client_real_auth.get("/v1/catalog", headers=headers)
    assert resp2.status_code == 200
    
    # Third request -> 429 Too Many Requests
    resp3 = test_client_real_auth.get("/v1/catalog", headers=headers)
    assert resp3.status_code == 429
    assert "Too many requests" in resp3.json()["detail"]

def test_payload_size_limit(monkeypatch, test_client_real_auth):
    # Set limit to 100 bytes
    monkeypatch.setattr(settings, "BILGEAPI_MAX_CONTENT_LENGTH", 100)
    
    # Small payload -> should work (under 100 bytes)
    small_payload = {"project_key": "x"}
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")
    resp = test_client_real_auth.post("/v1/incidents", json=small_payload)
    # Validation error 422 is fine, but it should not be 413
    assert resp.status_code == 422
    
    # Large payload -> 413 Content Too Large
    large_payload = {
        "project_key": "x" * 200,
        "error_message": "y" * 200
    }
    resp = test_client_real_auth.post("/v1/incidents", json=large_payload)
    assert resp.status_code == 413
    assert "entity too large" in resp.json()["detail"].lower()

def test_auth_rbac_audit_logging(monkeypatch, test_client_real_auth):
    # Set auth to api_key mode and log events
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["valid_key:operator"])
    
    # Trigger AUTH_FAILURE (missing key) and clear limits
    test_client_real_auth.get("/v1/catalog", headers={"X-Test-Clear-Limits": "true"})
    
    # Trigger RBAC_FAILURE (valid key but unauthorized route)
    headers = {"X-API-Key": "valid_key", "X-Test-Clear-Limits": "true"}
    test_client_real_auth.get("/v1/audit-events", headers=headers)
    
    # Retrieve audit events to verify failures are logged
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")
    audit_resp = test_client_real_auth.get("/v1/audit-events")
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    
    # Verify we have AUTH_FAILURE
    auth_failures = [e for e in events if e["event_type"] == "AUTH_FAILURE"]
    assert len(auth_failures) >= 1
    assert "Missing API key" in auth_failures[0]["metadata"]["reason"]
    
    # Verify we have RBAC_FAILURE
    rbac_failures = [e for e in events if e["event_type"] == "RBAC_FAILURE"]
    assert len(rbac_failures) >= 1
    assert "Missing required permission" in rbac_failures[0]["metadata"]["reason"]
