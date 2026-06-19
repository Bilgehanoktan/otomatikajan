import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
import httpx

from apps.bilgeapi.config import settings
from apps.bilgeapi.main import app
from apps.bilgeapi.adapters.registry import adapter_registry
from apps.bilgeapi.schemas.repair import ApprovalStatus, DispatchStatus, RepairRequestResponse

_ADAPTER_KEYS = [
    "BILGEAPI_WEBHOOK_URL",
    "BILGEAPI_WEBHOOK_SECRET",
    "BILGEAPI_GITHUB_ENABLED",
    "BILGEAPI_GITHUB_TOKEN",
    "BILGEAPI_GITHUB_OWNER",
    "BILGEAPI_GITHUB_REPO",
    "BILGEAPI_JIRA_ENABLED",
    "BILGEAPI_JIRA_BASE_URL",
    "BILGEAPI_JIRA_EMAIL",
    "BILGEAPI_JIRA_API_TOKEN",
    "BILGEAPI_SOVEREIGN_ENABLED",
    "BILGEAPI_SOVEREIGN_BASE_URL",
    "BILGEAPI_SOVEREIGN_API_KEY",
]

@pytest.fixture(autouse=True)
def _isolate_env():
    saved = {k: os.environ.get(k) for k in _ADAPTER_KEYS}
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

def _clean_env():
    for k in _ADAPTER_KEYS:
        os.environ.pop(k, None)

@pytest.mark.asyncio
class TestAdapters:

    async def test_adapter_registry_list_and_get(self):
        adapters = adapter_registry.list_adapters()
        assert len(adapters) == 6
        names = {a.name for a in adapters}
        assert names == {"webhook", "github_issue", "jira", "sovereign_repair_lab", "slack", "teams"}

        webhook = adapter_registry.get_adapter("webhook")
        assert webhook is not None
        assert webhook.name == "webhook"

        non_existent = adapter_registry.get_adapter("non_existent")
        assert non_existent is None

    async def test_webhook_adapter_health_and_dispatch(self):
        settings.BILGEAPI_WEBHOOK_URL = "http://8.8.8.8"
        webhook = adapter_registry.get_adapter("webhook")
        assert webhook.enabled is True
        assert webhook.configured is True
        
        # Test dry-run dispatch
        payload = {"test": "payload"}
        res = await webhook.dispatch("rep_123", payload, dry_run=True)
        assert res["status"] == "SENT"
        assert "webhook" in res["external_reference"]

    async def test_github_adapter_configuration_and_health(self):
        _clean_env()
        github = adapter_registry.get_adapter("github_issue")
        assert github.enabled is False
        assert github.configured is False

        # Set partial config
        settings.BILGEAPI_GITHUB_ENABLED = True
        settings.BILGEAPI_GITHUB_TOKEN = "token"
        assert github.enabled is True
        assert github.configured is False

        # Set full config
        settings.BILGEAPI_GITHUB_OWNER = "owner"
        settings.BILGEAPI_GITHUB_REPO = "repo"
        assert github.configured is True

        # Test health check mocking successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            health = await github.health_check()
            assert health == "healthy"

        # Test health check mocking failure response
        mock_response.status_code = 401
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            health = await github.health_check()
            assert health == "unhealthy"

        # Test health check disabled state
        settings.BILGEAPI_GITHUB_ENABLED = False
        health = await github.health_check()
        assert health == "disabled"

    async def test_github_adapter_dispatch_dry_run(self):
        settings.BILGEAPI_GITHUB_ENABLED = True
        settings.BILGEAPI_GITHUB_TOKEN = "token"
        settings.BILGEAPI_GITHUB_OWNER = "owner"
        settings.BILGEAPI_GITHUB_REPO = "repo"

        github = adapter_registry.get_adapter("github_issue")
        payload = {
            "repair_request": {"risk_score": 0.5, "risk_reason": "High risk env"},
            "incident": {"severity": "HIGH", "source_system": "backend", "project_key": "payment", "error_message": "Postgres Pool Exhausted"},
            "diagnostic": {"root_cause_hypothesis": "Too many idle connections", "confidence": 0.9}
        }
        res = await github.dispatch("rep_123", payload, dry_run=True)
        assert res["status"] == "SENT"
        assert "github:" in res["external_reference"]

    async def test_jira_adapter_configuration_and_health(self):
        _clean_env()
        jira = adapter_registry.get_adapter("jira")
        assert jira.enabled is False
        assert jira.configured is False

        settings.BILGEAPI_JIRA_ENABLED = True
        settings.BILGEAPI_JIRA_BASE_URL = "https://company.atlassian.net"
        settings.BILGEAPI_JIRA_EMAIL = "admin@company.com"
        settings.BILGEAPI_JIRA_API_TOKEN = "api_token"
        assert jira.enabled is True
        assert jira.configured is True

        # Test health check mocking successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            health = await jira.health_check()
            assert health == "healthy"

        # Test health check disabled state
        settings.BILGEAPI_JIRA_ENABLED = False
        health = await jira.health_check()
        assert health == "disabled"

    async def test_sovereign_adapter_configuration_and_health(self):
        _clean_env()
        sovereign = adapter_registry.get_adapter("sovereign_repair_lab")
        assert sovereign.enabled is False
        assert sovereign.configured is False

        settings.BILGEAPI_SOVEREIGN_ENABLED = True
        settings.BILGEAPI_SOVEREIGN_BASE_URL = "http://app:8000"
        settings.BILGEAPI_SOVEREIGN_API_KEY = "api_key"
        assert sovereign.enabled is True
        assert sovereign.configured is True

        # Test health check mocking successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            health = await sovereign.health_check()
            assert health == "healthy"

        # Test health check disabled state
        settings.BILGEAPI_SOVEREIGN_ENABLED = False
        health = await sovereign.health_check()
        assert health == "disabled"

    async def test_adapters_router_endpoints_without_auth_fails(self, test_client):
        # Temporarily enable API key authentication
        settings.BILGEAPI_AUTH_MODE = "api_key"
        settings.BILGEAPI_STATIC_KEYS = "admin_key:admin,op_key:operator"
        try:
            # 1. No key -> 401
            resp = test_client.get("/v1/adapters")
            assert resp.status_code == 401

            # 2. Key with operator role (missing bilgeapi.admin permission) -> 403
            resp = test_client.get("/v1/adapters", headers={"X-API-Key": "op_key"})
            assert resp.status_code == 403
        finally:
            settings.BILGEAPI_AUTH_MODE = "disabled"

    async def test_adapters_router_list_and_health_with_admin_auth(self, test_client):
        # Temporarily enable API key authentication
        settings.BILGEAPI_AUTH_MODE = "api_key"
        settings.BILGEAPI_STATIC_KEYS = "admin_key:admin,op_key:operator"
        try:
            resp = test_client.get("/v1/adapters", headers={"X-API-Key": "admin_key"})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 6
            adapter_names = {a["name"] for a in data}
            assert "github_issue" in adapter_names

            # GET single adapter health
            resp = test_client.get("/v1/adapters/github_issue/health", headers={"X-API-Key": "admin_key"})
            assert resp.status_code == 200
            health_data = resp.json()
            assert health_data["name"] == "github_issue"
            assert "health" in health_data

            # GET non-existent health -> 404
            resp = test_client.get("/v1/adapters/non_existent/health", headers={"X-API-Key": "admin_key"})
            assert resp.status_code == 404
        finally:
            settings.BILGEAPI_AUTH_MODE = "disabled"

    async def test_repairs_dispatch_endpoint_updated_to_use_adapters(self, test_client):
        # Setup mock db and models in memory repositories
        from apps.bilgeapi.repositories.memory import memory_repositories
        from apps.bilgeapi.schemas.repair import ApprovalStatus, DispatchStatus

        # Add dummy incident and diagnostic for enrichment
        from apps.bilgeapi.schemas.incident import IncidentResponse, Severity
        memory_repositories.incidents["inc_123"] = IncidentResponse(
            id="inc_123",
            project_key="proj",
            source_system="sys",
            environment="dev",
            kind="db",
            severity=Severity.HIGH,
            error_message="err",
            occurred_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )

        from apps.bilgeapi.schemas.diagnostic import DiagnosticResult, DiagnosticStatus
        memory_repositories.diagnostics["diag_123"] = DiagnosticResult(
            diagnostic_id="diag_123",
            incident_id="inc_123",
            status=DiagnosticStatus.COMPLETED,
            confidence=0.9,
            created_at=datetime.now(timezone.utc)
        )

        repair_id = "rep_adapters_test_123"
        memory_repositories.repair_requests[repair_id] = RepairRequestResponse(
            id=repair_id,
            diagnostic_id="diag_123",
            requested_by="test-admin",
            approved_by=None,
            approval_status=ApprovalStatus.APPROVED,
            risk_score=0.1,
            risk_reason="Low risk",
            dispatch_status=DispatchStatus.PENDING,
            external_reference=None,
            approval_required=True,
            rejection_reason=None,
            approved_at=datetime.now(timezone.utc),
            rejected_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        settings.BILGEAPI_GITHUB_ENABLED = True
        settings.BILGEAPI_GITHUB_TOKEN = "token"
        settings.BILGEAPI_GITHUB_OWNER = "owner"
        settings.BILGEAPI_GITHUB_REPO = "repo"

        # POST /v1/repair-requests/{id}/dispatch with github_issue adapter and dry_run=True
        resp = test_client.post(
            f"/v1/repair-requests/{repair_id}/dispatch",
            json={"adapter": "github_issue", "dry_run": True}
        )
        assert resp.status_code == 200
        
        # Since the dispatch executes in background task using asyncio.create_task,
        # we yield control to allow it to run
        import asyncio
        await asyncio.sleep(0.1)
        
        # Reload from repository to check dispatch_status
        reloaded = memory_repositories.repair_requests[repair_id]
        assert reloaded.dispatch_status == DispatchStatus.DISPATCHED
        assert reloaded.external_reference is not None
        assert "github:" in reloaded.external_reference
