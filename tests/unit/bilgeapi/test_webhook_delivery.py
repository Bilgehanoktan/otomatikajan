import pytest
import asyncio
import hmac
import hashlib
import json
import jwt
from datetime import datetime, timezone, timedelta
import httpx
from fastapi import HTTPException
from apps.bilgeapi.config import settings
from apps.bilgeapi.adapters.webhook import is_ssrf_safe, generate_signature, WebhookDispatcher
from apps.bilgeapi.services.webhook import WebhookDeliveryService
from apps.bilgeapi.schemas.repair import RepairRequestCreate, ApprovalStatus, DispatchStatus
from apps.bilgeapi.schemas.webhook import WebhookTestRequest
from apps.bilgeapi.repositories.memory import (
    InMemoryRepairRequestRepository,
    InMemoryWebhookDeliveryRepository,
    InMemoryAuditRepository
)
from apps.bilgeapi.services.audit import AuditService

# --- SSRF Guard Tests ---

def test_is_ssrf_safe_public_domain(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    # Resolve domain to public IP (e.g. google.com resolved IP shouldn't be local/private)
    assert is_ssrf_safe("https://google.com") is True

def test_is_ssrf_safe_blocked_locals(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    # Loopback
    assert is_ssrf_safe("http://127.0.0.1") is False
    assert is_ssrf_safe("http://localhost") is False
    assert is_ssrf_safe("http://[::1]") is False
    # Private subnets
    assert is_ssrf_safe("http://192.168.1.50") is False
    assert is_ssrf_safe("http://10.0.0.1") is False
    assert is_ssrf_safe("http://172.16.0.100") is False
    # Link local / Cloud metadata
    assert is_ssrf_safe("http://169.254.169.254") is False
    assert is_ssrf_safe("http://169.254.10.10") is False

def test_is_ssrf_safe_private_bypass_dev(monkeypatch):
    # Allow private in development/test
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", True)
    assert is_ssrf_safe("http://127.0.0.1", allow_private=True) is True

def test_is_ssrf_safe_private_bypass_production(monkeypatch):
    # Strictly block in production regardless of allow_private flag
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", True)
    
    # Check that settings enforces False on APP_ENV == production
    assert settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS is False
    # SSRF guard forces allow_private=False
    assert is_ssrf_safe("http://127.0.0.1", allow_private=True) is False

def test_production_webhook_secret_enforcement(monkeypatch):
    # Default secret in production -> RuntimeError
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BILGEAPI_WEBHOOK_SECRET", "webhook_secret")
    with pytest.raises(RuntimeError, match="Production mode requires a secure and custom"):
        _ = settings.BILGEAPI_WEBHOOK_SECRET

    # Custom secret in production -> works
    monkeypatch.setenv("BILGEAPI_WEBHOOK_SECRET", "my_super_secure_key_123_abc")
    assert settings.BILGEAPI_WEBHOOK_SECRET == "my_super_secure_key_123_abc"


# --- Signature Generation Test ---

def test_generate_signature():
    payload = '{"test": "data"}'
    secret = "key_secret"
    sig = generate_signature(payload, secret)
    expected = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    assert sig == expected

# --- Redirect Rejection & Timeout Test ---

@pytest.mark.asyncio
async def test_webhook_dispatcher_redirect_and_timeout(monkeypatch):
    dispatcher = WebhookDispatcher()
    
    # Verify timeout parameter is correctly registered from settings
    assert dispatcher.client.timeout.read == float(settings.BILGEAPI_WEBHOOK_TIMEOUT)
    
    # Mock httpx AsyncClient post request to ensure redirects are NOT followed
    async def mock_post(url, content, headers, follow_redirects):
        assert follow_redirects is False
        return httpx.Response(301, headers={"Location": "https://example.com/other"})
        
    monkeypatch.setattr(dispatcher.client, "post", mock_post)
    
    response = await dispatcher.dispatch(
        url="https://google.com",
        payload={"x": 1},
        signature_secret="secret",
        idempotency_key="key",
        timestamp="now"
    )
    
    assert response.status_code == 301
    await dispatcher.close()

# --- Background Retry & State Machine Tests ---

@pytest.mark.asyncio
async def test_webhook_delivery_service_workflow(monkeypatch):
    # Setup in-memory repos and service
    webhook_repo = InMemoryWebhookDeliveryRepository()
    repair_repo = InMemoryRepairRequestRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)
    
    service = WebhookDeliveryService(
        webhook_repo=webhook_repo,
        repair_repo=repair_repo,
        audit_service=audit_service
    )
    
    # Configure parameters
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", True)
    monkeypatch.setattr(settings, "BILGEAPI_WEBHOOK_MAX_RETRIES", 3)
    monkeypatch.setattr(settings, "BILGEAPI_WEBHOOK_BACKOFF_FACTOR", 0.01) # fast tests
    
    # Ingest incident & diagnostic mock IDs, create pending repair request
    repair_create = RepairRequestCreate(requested_by="operator", risk_score=0.2, risk_reason="restart")
    repair_req = await repair_repo.create("diag_123", repair_create)
    
    # 1. Test SUCCESSFUL webhook dispatch (mock returning HTTP 200)
    async def mock_dispatch_success(*args, **kwargs):
        return httpx.Response(200, content=b"{}")
    monkeypatch.setattr(service.dispatcher, "dispatch", mock_dispatch_success)
    
    delivery = await service.dispatch_webhook(
        repair_request_id=repair_req.id,
        webhook_url="https://google.com/webhook",
        payload={"repair_id": repair_req.id}
    )
    
    assert delivery["delivery_status"] == "PENDING"
    
    # Wait for the async task to execute using real sleep to yield control
    await asyncio.sleep(0.1)
    
    # Retrieve updated delivery log from repo
    updated_delivery = await webhook_repo.get_delivery(delivery["id"])
    assert updated_delivery is not None
    assert updated_delivery["delivery_status"] == "SENT"
    assert updated_delivery["status_code"] == 200
    
    # Verify repair request is updated to DISPATCHED
    updated_repair = await repair_repo.get(repair_req.id)
    assert updated_repair.dispatch_status == DispatchStatus.DISPATCHED.value
    
    # Verify audit event for WEBHOOK_SENT
    audits = await audit_repo.list_recent()
    assert any(e.event_type == "WEBHOOK_SENT" and e.entity_id == delivery["id"] for e in audits)

    # 2. Test FAILING webhook dispatch transitioning to DEAD_LETTER
    repair_req2 = await repair_repo.create("diag_456", repair_create)
    
    async def mock_dispatch_fail(*args, **kwargs):
        raise httpx.ConnectError("Connection refused")
    monkeypatch.setattr(service.dispatcher, "dispatch", mock_dispatch_fail)
    
    delivery2 = await service.dispatch_webhook(
        repair_request_id=repair_req2.id,
        webhook_url="https://google.com/webhook-fail",
        payload={"repair_id": repair_req2.id}
    )
    
    # Wait for the async task and its retries to execute
    await asyncio.sleep(0.1)
    
    updated_delivery2 = await webhook_repo.get_delivery(delivery2["id"])
    assert updated_delivery2 is not None
    assert updated_delivery2["delivery_status"] == "DEAD_LETTER"
    assert updated_delivery2["attempt_count"] == 3.0
    assert "Connection refused" in updated_delivery2["error_message"]
    
    # Verify repair request is marked as FAILED
    updated_repair2 = await repair_repo.get(repair_req2.id)
    assert updated_repair2.dispatch_status == DispatchStatus.FAILED.value
    
    # Verify audit event for WEBHOOK_DEAD_LETTER
    audits = await audit_repo.list_recent()
    assert any(e.event_type == "WEBHOOK_DEAD_LETTER" and e.entity_id == delivery2["id"] for e in audits)

# --- Test Router Endpoints ---

def test_webhook_test_endpoint_sent(test_client, monkeypatch):
    # Bypass auth and mock httpx client post to return 200
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", True)
    
    # Mock post call inside router
    async def mock_post(*args, **kwargs):
        return httpx.Response(200, content=b"{}")
        
    # We must patch httpx.AsyncClient.post inside test context
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    test_req = {
        "webhook_url": "http://127.0.0.1:8100/v1/health", # private but allowed by override
        "payload": {"ping": "pong"}
    }
    
    response = test_client.post("/v1/webhooks/test", json=test_req)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SENT"
    assert data["status_code"] == 200
    assert data["signature"] is not None

def test_webhook_test_endpoint_ssrf_blocked(test_client, monkeypatch):
    # Bypass auth but keep allow_private_webhooks False (default)
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", False)
    
    test_req = {
        "webhook_url": "http://127.0.0.1:8100/v1/health",
        "payload": {"ping": "pong"}
    }
    
    response = test_client.post("/v1/webhooks/test", json=test_req)
    # SSRF blocks loopback, returns 400 Bad Request
    assert response.status_code == 400
    assert "SSRF Guard" in response.json()["detail"]

def test_webhook_test_endpoint_rbac_restricted(monkeypatch, test_client_real_auth):
    # Enable JWT and verify OPERATOR cannot run webhooks test (requires bilgeapi.admin)
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "jwt")
    monkeypatch.setattr(settings, "BILGEAPI_JWT_SECRET", "secret")
    
    op_token = jwt.encode({
        "sub": "user_op_1",
        "role": "operator",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
    }, "secret", algorithm="HS256")
    headers_op = {"Authorization": f"Bearer {op_token}"}
    
    test_req = {
        "webhook_url": "https://google.com",
        "payload": {}
    }
    
    response = test_client_real_auth.post("/v1/webhooks/test", json=test_req, headers=headers_op)
    assert response.status_code == 403 # Forbidden for OPERATOR

    # ADMIN token works
    admin_token = jwt.encode({
        "sub": "user_admin",
        "role": "admin",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
    }, "secret", algorithm="HS256")
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    
    # Mock post call inside router
    async def mock_post(*args, **kwargs):
        return httpx.Response(200, content=b"{}")
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    response = test_client_real_auth.post("/v1/webhooks/test", json=test_req, headers=headers_admin)
    assert response.status_code == 200

def test_repairs_endpoints_lifecycle(test_client, monkeypatch):
    # Disable auth
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", True)
    
    # Mock post call for dispatch
    async def mock_post(*args, **kwargs):
        return httpx.Response(200, content=b"{}")
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    # 1. Create repair request using query params Depends
    resp = test_client.post("/v1/repair-requests?diagnostic_id=diag_123&requested_by=operator&risk_score=0.1&risk_reason=low")
    assert resp.status_code == 201
    rep_id = resp.json()["id"]
    assert rep_id.startswith("rep_")

    # 2. Create repair request using JSON body
    resp_json = test_client.post("/v1/repair-requests/json?diagnostic_id=diag_456", json={
        "requested_by": "operator2",
        "risk_score": 0.3,
        "risk_reason": "medium"
    })
    assert resp_json.status_code == 201
    assert resp_json.json()["id"].startswith("rep_")

    # 3. Retrieve request details
    get_resp = test_client.get(f"/v1/repair-requests/{rep_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == rep_id
    assert get_resp.json()["approval_status"] == "PENDING"

    # 4. Approve request
    app_resp = test_client.post(f"/v1/repair-requests/{rep_id}/approve")
    assert app_resp.status_code == 200
    assert app_resp.json()["approval_status"] == "APPROVED"

    # 4.5 Dispatch request
    disp_resp = test_client.post(f"/v1/repair-requests/{rep_id}/dispatch", json={
        "webhook_url": "https://google.com/webhook"
    })
    assert disp_resp.status_code == 200

    # 5. Retrieve webhook deliveries
    web_resp = test_client.get("/v1/webhook-deliveries")
    assert web_resp.status_code == 200
    deliveries = web_resp.json()
    assert len(deliveries) >= 1
    assert any(d["repair_request_id"] == rep_id for d in deliveries)

def test_repairs_endpoints_not_found(test_client, monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "disabled")
    
    resp = test_client.get("/v1/repair-requests/nonexistent")
    assert resp.status_code == 404
    
    resp = test_client.post("/v1/repair-requests/nonexistent/approve", json={"webhook_url": "https://google.com"})
    assert resp.status_code == 404

def test_production_webhook_secret_enforcement_empty(monkeypatch):
    # Empty secret in production -> RuntimeError
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BILGEAPI_WEBHOOK_SECRET", "")
    with pytest.raises(RuntimeError, match="Production mode requires a secure and custom"):
        _ = settings.BILGEAPI_WEBHOOK_SECRET

def test_production_allow_private_webhooks_forced_false(monkeypatch):
    # Enforce false in production even if set to true in env
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", "true")
    assert settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS is False

def test_ssrf_guard_dns_resolving_to_private_ip(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", False)
    
    import socket
    def mock_getaddrinfo(host, port, *args, **kwargs):
        if host == "malicious.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.100", 80))]
        raise socket.gaierror("Name or service not known")
        
    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)
    assert is_ssrf_safe("http://malicious.com/webhook") is False

def test_ssrf_guard_blocks_metadata_and_special_ips(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", False)
    
    import socket
    def mock_getaddrinfo(host, port, *args, **kwargs):
        if host == "metadata.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80))]
        elif host == "multicast.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("224.0.0.1", 80))]
        elif host == "unspecified.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("0.0.0.0", 80))]
        raise socket.gaierror()
        
    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)
    assert is_ssrf_safe("http://metadata.com") is False
    assert is_ssrf_safe("http://multicast.com") is False
    assert is_ssrf_safe("http://unspecified.com") is False

@pytest.mark.asyncio
async def test_webhook_delivery_service_ssrf_immediate_failure(monkeypatch):
    webhook_repo = InMemoryWebhookDeliveryRepository()
    repair_repo = InMemoryRepairRequestRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)
    
    service = WebhookDeliveryService(
        webhook_repo=webhook_repo,
        repair_repo=repair_repo,
        audit_service=audit_service
    )
    
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setattr(settings, "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", False)
    
    repair_create = RepairRequestCreate(requested_by="operator", risk_score=0.2, risk_reason="test")
    repair_req = await repair_repo.create("diag_123", repair_create)
    
    delivery = await service.dispatch_webhook(
        repair_request_id=repair_req.id,
        webhook_url="http://127.0.0.1/webhook", # private IP
        payload={}
    )
    
    # Wait for background dispatch to execute
    await asyncio.sleep(0.05)
    
    updated_delivery = await webhook_repo.get_delivery(delivery["id"])
    assert updated_delivery["delivery_status"] == "DEAD_LETTER"
    assert "SSRF Guard" in updated_delivery["error_message"]
    
    updated_repair = await repair_repo.get(repair_req.id)
    assert updated_repair.dispatch_status == DispatchStatus.FAILED.value

def test_openapi_public_paths_exempt_from_security():
    from apps.bilgeapi.main import app
    schema = app.openapi()
    
    # Assert security schemes exist in components
    assert "securitySchemes" in schema["components"]
    assert "ApiKeyHeader" in schema["components"]["securitySchemes"]
    assert "BearerAuth" in schema["components"]["securitySchemes"]
    
    # Public paths should NOT have security key
    assert "security" not in schema["paths"]["/health"]["get"]
    
    # Protected paths (e.g. /v1/incidents) MUST have security requirements
    assert "security" in schema["paths"]["/v1/incidents"]["post"]
    assert schema["paths"]["/v1/incidents"]["post"]["security"] == [
        {"ApiKeyHeader": []},
        {"BearerAuth": []}
    ]


