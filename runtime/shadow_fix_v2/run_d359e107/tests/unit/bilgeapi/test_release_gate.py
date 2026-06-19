import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from httpx import Response
import httpx

from apps.bilgeapi.config import settings
from apps.bilgeapi.repositories.memory import InMemoryReleaseCheckRepository
from apps.bilgeapi.services.release import BilgeAPIReleaseGate
from apps.bilgeapi.main import app as real_app
from apps.bilgeapi.routers.deps import get_release_repository, get_release_gate_service

_RELEASE_KEYS = [
    "APP_ENV",
    "BILGEAPI_JWT_SECRET",
    "BILGEAPI_JWT_SECRETS",
    "BILGEAPI_WEBHOOK_SECRET",
    "BILGEAPI_DATABASE_URL",
    "DATABASE_URL",
    "BILGEAPI_AUTH_MODE",
    "BILGEAPI_CORS_ALLOWLIST",
    "BILGEAPI_ALLOW_PRIVATE_WEBHOOKS",
    "BILGEAPI_STATIC_KEYS",
    "BILGEAPI_STATIC_KEY_HASHES",
]

@pytest.fixture(autouse=True)
def _isolate_env():
    saved = {k: os.environ.get(k) for k in _RELEASE_KEYS}
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

def _clean_env():
    for k in _RELEASE_KEYS:
        os.environ.pop(k, None)

@pytest.mark.asyncio
class TestReleaseGate:

    async def test_check_modules_passes(self):
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)
        res = gate.check_modules()
        # Verify core module check succeeds for main apps/libs
        assert res["apps.bilgeapi.config"] == "OK"
        assert res["apps.bilgeapi.main"] == "OK"

    async def test_check_endpoints_identifies_registered_routes(self):
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)
        
        # Test against real_app
        res = gate.check_endpoints(real_app)
        assert res["/health"] == "VERIFIED_PRESENT"
        assert res["/v1/incidents"] == "VERIFIED_PRESENT"
        assert res["/v1/repair-requests"] == "VERIFIED_PRESENT"

    async def test_check_security_config_in_development(self):
        _clean_env()
        os.environ["APP_ENV"] = "development"
        
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)
        res = gate.check_security_config()
        # In development, missing secrets/wildcards are warnings, not blockers
        assert len(res["blockers"]) == 0
        assert res["security_hardened"] is True

    async def test_check_security_config_in_production_blocked_by_defaults(self):
        _clean_env()
        os.environ["APP_ENV"] = "production"
        settings.BILGEAPI_WEBHOOK_SECRET = "webhook_secret" # Default
        
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)
        res = gate.check_security_config()
        assert len(res["blockers"]) > 0
        assert any("BILGEAPI_WEBHOOK_SECRET" in b for b in res["blockers"])
        assert res["security_hardened"] is False

    async def test_check_security_config_in_production_blocked_by_sqlite_db(self):
        _clean_env()
        os.environ["APP_ENV"] = "production"
        settings.BILGEAPI_WEBHOOK_SECRET = "secure-webhook-secret-1234"
        settings.BILGEAPI_DATABASE_URL = "sqlite+aiosqlite:///cortex.db"
        settings.BILGEAPI_CORS_ALLOWLIST = ["https://app.domain.com"]
        settings.BILGEAPI_AUTH_MODE = "api_key"
        
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)
        res = gate.check_security_config()
        assert any("database URL" in b for b in res["blockers"])

    async def test_release_gate_dry_run_does_not_mutate_db_or_send_webhook(self):
        """
        Verifies that E2E dry-run smoke test works completely in-memory,
        does not call external APIs, and does not mutate real DB state.
        """
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        # Mock the webhook client call so it returns status 200
        mock_dispatcher = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_dispatcher.dispatch.return_value = mock_response

        trace = await gate.run_e2e_dry_run(dispatcher=mock_dispatcher)
        
        # Webhook dispatcher should have been called exactly once during trace run
        mock_dispatcher.dispatch.assert_called_once()
        
        # Verify E2E trace steps are recorded
        assert len(trace) >= 6
        assert any(step["action"] == "INCIDENT_INTAKE" for step in trace)
        assert any(step["action"] == "DIAGNOSTIC_RUN_INITIATE" for step in trace)
        assert any(step["action"] == "DIAGNOSTIC_EVALUATION" for step in trace)
        assert any(step["action"] == "RISK_SCORING" for step in trace)
        assert any(step["action"] == "REPAIR_REQUEST_PREPARATION" for step in trace)
        assert any(step["action"] == "WEBHOOK_DISPATCH_SIMULATION" for step in trace)
        assert all(step["status"] == "PASSED" for step in trace)

    async def test_execute_readiness_audit_score_calculation(self):
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)
        
        # Test in development with warnings
        _clean_env()
        os.environ["APP_ENV"] = "development"
        # Avoid plaintext keys warning by using key hashes instead
        os.environ["BILGEAPI_STATIC_KEY_HASHES"] = "somehash_16chars:admin"
        settings.BILGEAPI_WEBHOOK_SECRET = "webhook_secret" # generates 1 warning

        # Mock check_test_and_coverage and check_database_migrations to avoid extra warnings
        with patch.object(gate, "check_test_and_coverage", return_value={"coverage_pct": 85.0, "passed_tests": 10, "failed_tests": 0, "source": "mock", "blockers": [], "warnings": []}):
            with patch.object(gate, "check_database_migrations", return_value={"head_revision": "rev1", "current_revision": "rev1", "blockers": [], "warnings": []}):
                with patch("apps.bilgeapi.main.REDIS_FALLBACK_ACTIVE", False):
                    check_data = await gate.execute_readiness_audit()
                    assert check_data["score"] == 95.0 # 100 - 5 = 95
                    assert check_data["status"] == "WARNING" # score >= 90 but warnings exist

    async def test_security_headers_middleware_active_on_non_public_paths(self):
        from fastapi.testclient import TestClient
        client = TestClient(real_app)

        # Mock auth dependency
        with patch("apps.bilgeapi.auth.require_permission", return_value=lambda: {"user": "admin"}):
            # GET protected path
            response = client.get("/v1/catalog", headers={"X-API-Key": "dev-test-key-001"})
            assert response.status_code == 200
            assert response.headers["X-Frame-Options"] == "DENY"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["X-XSS-Protection"] == "1; mode=block"
            assert "Content-Security-Policy" in response.headers

    async def test_security_headers_middleware_bypassed_on_public_paths(self):
        from fastapi.testclient import TestClient
        client = TestClient(real_app)

        # GET /health should have basic security headers (nosniff, X-Frame-Options)
        # but NOT strict CSP (sandbox) — Phase 10 policy
        response = client.get("/health")
        assert response.status_code == 200
        assert "Content-Security-Policy" not in response.headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

        # GET /docs should NOT have any security headers (Swagger UI needs inline scripts)
        response = client.get("/docs")
        assert "Content-Security-Policy" not in response.headers

    async def test_global_exception_handler_masking(self):
        from fastapi.testclient import TestClient
        
        # Temporarily register a route that throws unexpected exception
        @real_app.get("/test-unhandled-exception")
        async def throw_error():
            raise ZeroDivisionError("Simulated division by zero")

        client = TestClient(real_app, raise_server_exceptions=False)
        response = client.get("/test-unhandled-exception")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal Server Error"}

    async def test_global_exception_handler_exceptions_not_masked(self):
        from fastapi.testclient import TestClient
        
        # Test HTTPException (like 404 Not Found) is not masked
        client = TestClient(real_app)
        response = client.get("/v1/non-existent-route-path")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}

    async def test_global_exception_handler_validation_error_not_masked(self):
        from fastapi.testclient import TestClient
        client = TestClient(real_app)
        # Post invalid payload to trigger 422
        response = client.post("/v1/release/readiness", json={"triggered_by": 12345}) # should be string
        assert response.status_code == 422

    async def test_release_router_endpoints(self, test_client):
        # Override the dependency for release repository with an in-memory one
        repo = InMemoryReleaseCheckRepository()
        real_app.dependency_overrides[get_release_repository] = lambda: repo
        
        try:
            # 1. GET latest before any checks -> 404
            response = test_client.get("/v1/release/readiness/latest")
            assert response.status_code == 404
            
            # 2. POST to run a check
            response = test_client.post("/v1/release/readiness", json={"triggered_by": "test-suite"})
            assert response.status_code == 200
            data = response.json()
            assert data["triggered_by"] == "test-suite"
            assert "score" in data
            assert "status" in data
            
            # 3. GET all checks
            response = test_client.get("/v1/release/readiness?limit=5")
            assert response.status_code == 200
            checks = response.json()
            assert len(checks) == 1
            
            # 4. GET latest check -> 200
            response = test_client.get("/v1/release/readiness/latest")
            assert response.status_code == 200
            assert response.json()["id"] == data["id"]
        finally:
            real_app.dependency_overrides.clear()

    async def test_postgres_repo_create_check(self):
        from apps.bilgeapi.repositories.postgres import PostgresReleaseCheckRepository
        from apps.bilgeapi.models.database import ReleaseCheckModel
        
        mock_db = AsyncMock()
        repo = PostgresReleaseCheckRepository(mock_db)
        
        check_data = {
            "status": "PASSED",
            "score": 100.0,
            "blockers": [],
            "warnings": [],
            "checked_modules": {},
            "checked_endpoints": {},
            "smoke_trace": [],
            "app_version": "1.0.0",
            "git_sha": "abc",
            "environment": "test",
            "triggered_by": "admin"
        }
        res = await repo.create_check(check_data)
        
        assert res["status"] == "PASSED"
        assert res["score"] == 100.0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_postgres_repo_get_latest_check(self):
        from apps.bilgeapi.repositories.postgres import PostgresReleaseCheckRepository
        from apps.bilgeapi.models.database import ReleaseCheckModel
        
        mock_db = AsyncMock()
        repo = PostgresReleaseCheckRepository(mock_db)
        
        mock_model = ReleaseCheckModel(
            id="rel_123",
            status="PASSED",
            score=100.0,
            blockers=[],
            warnings=[],
            checked_modules={},
            checked_endpoints={},
            smoke_trace=[],
            app_version="1.0.0",
            git_sha="abc",
            environment="test",
            triggered_by="admin",
            created_at=datetime.now(timezone.utc)
        )
        
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = mock_model
        mock_db.execute.return_value = mock_execute_result
        
        res = await repo.get_latest_check()
        assert res["id"] == "rel_123"
        assert res["status"] == "PASSED"
        mock_db.execute.assert_called_once()

    async def test_postgres_repo_get_latest_check_none(self):
        from apps.bilgeapi.repositories.postgres import PostgresReleaseCheckRepository
        
        mock_db = AsyncMock()
        repo = PostgresReleaseCheckRepository(mock_db)
        
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_execute_result
        
        res = await repo.get_latest_check()
        assert res is None

    async def test_postgres_repo_list_checks(self):
        from apps.bilgeapi.repositories.postgres import PostgresReleaseCheckRepository
        from apps.bilgeapi.models.database import ReleaseCheckModel
        
        mock_db = AsyncMock()
        repo = PostgresReleaseCheckRepository(mock_db)
        
        mock_model = ReleaseCheckModel(
            id="rel_123",
            status="PASSED",
            score=100.0,
            blockers=[],
            warnings=[],
            checked_modules={},
            checked_endpoints={},
            smoke_trace=[],
            app_version="1.0.0",
            git_sha="abc",
            environment="test",
            triggered_by="admin",
            created_at=datetime.now(timezone.utc)
        )
        
        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value.all.return_value = [mock_model]
        mock_db.execute.return_value = mock_execute_result
        
        res = await repo.list_checks(limit=10)
        assert len(res) == 1
        assert res[0]["id"] == "rel_123"
        mock_db.execute.assert_called_once()

    async def test_risk_scoring_service_matrix(self):
        from apps.bilgeapi.services.risk import RiskScoringService
        from apps.bilgeapi.schemas.incident import IncidentResponse, Severity as IncSeverity
        from apps.bilgeapi.schemas.diagnostic import DiagnosticResult, DiagnosticStatus
        
        service = RiskScoringService()
        
        # Test permutations for 100% coverage on risk.py
        envs = ["production", "staging", "development"]
        sevs = ["critical", "high", "medium", "low"]
        kinds = ["security_breach", "database_lag", "resource_leak", "other_incident"]
        keywords_list = [
            ("delete database", True, False, True, False), # has_crit, has_sec, has_db, has_wf
            ("secret key reset", False, True, False, False),
            ("checkout migration", False, False, True, True),
        ]
        
        for env in envs:
            for sev in sevs:
                for kind in kinds:
                    for kw, crit, sec, db, wf in keywords_list:
                        incident = IncidentResponse(
                            id="inc_123",
                            project_key="proj",
                            source_system="sys",
                            environment=env,
                            kind=kind,
                            severity=IncSeverity.HIGH if sev == "high" else IncSeverity.CRITICAL if sev == "critical" else IncSeverity.MEDIUM,
                            error_message="err",
                            occurred_at=datetime.now(timezone.utc),
                            created_at=datetime.now(timezone.utc)
                        )
                        # Override severity name for testing specific strings
                        incident.severity = sev
                        
                        diagnostic = DiagnosticResult(
                            diagnostic_id="diag_123",
                            incident_id="inc_123",
                            status=DiagnosticStatus.COMPLETED,
                            confidence=0.8,
                            recommendations=[{"description": kw}],
                            created_at=datetime.now(timezone.utc)
                        )
                        
                        score, reason = service.calculate_risk(incident, diagnostic)
                        assert 0.0 <= score <= 1.0

    async def test_postgres_other_repos(self):
        from apps.bilgeapi.repositories.postgres import (
            PostgresIncidentRepository,
            PostgresDiagnosticRepository,
            PostgresFindingRepository,
            PostgresRecommendationRepository,
            PostgresRepairRequestRepository,
            PostgresAuditRepository,
            PostgresWebhookDeliveryRepository
        )
        from apps.bilgeapi.schemas.incident import IncidentCreate, Severity
        from apps.bilgeapi.schemas.repair import RepairRequestCreate, ApprovalStatus, DispatchStatus
        mock_db = AsyncMock()
        
        def mock_refresh(model):
            model.id = "mock-id-123"
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.approved_at = datetime.now(timezone.utc)
            model.rejected_at = datetime.now(timezone.utc)
            model.started_at = datetime.now(timezone.utc)
            model.completed_at = datetime.now(timezone.utc)
            model.occurred_at = datetime.now(timezone.utc)
            model.metadata_fields = {}
            model.tags = []
            model.stack_trace = None
            model.correlation_id = None
            model.diagnostic_id = "diag_123"
            model.finding_id = "find_123"
            model.recommendation_id = "rec_123"
            model.repair_request_id = "rep_123"
            model.webhook_url = "url"
            model.status_code = 200
            model.delivery_status = "SENT"
            model.payload_hash = "abc"
            model.attempt_count = 1
            model.rejection_reason = None
            model.actor_id = "user"
            model.actor_type = "op"
            model.entity_type = "entity"
            model.entity_id = "123"
            model.event_type = "test"
            
        mock_db.refresh.side_effect = mock_refresh
        
        from apps.bilgeapi.models.database import (
            IncidentModel, DiagnosticRunModel, FindingModel,
            RecommendationModel, RepairRequestModel, AuditEventModel, WebhookDeliveryModel
        )
        
        dummy_incident = IncidentModel(
            id="inc_123", project_key="proj", source_system="sys",
            environment="dev", kind="db", severity="HIGH", error_message="err",
            occurred_at=datetime.now(timezone.utc), created_at=datetime.now(timezone.utc),
            stack_trace=None, correlation_id="corr_123",
            tags=[], metadata_fields={}
        )
        
        dummy_diagnostic = DiagnosticRunModel(
            diagnostic_id="diag_123", incident_id="inc_123", status="COMPLETED",
            confidence=0.9, created_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc)
        )
        
        dummy_finding = FindingModel(
            id="find_123", diagnostic_id="diag_123", description="finding-desc",
            metadata_fields={}
        )
        
        dummy_recommendation = RecommendationModel(
            id="rec_123", diagnostic_id="diag_123", description="rec-desc",
            metadata_fields={}
        )
        
        dummy_repair = RepairRequestModel(
            id="rep_123", diagnostic_id="diag_123", requested_by="user",
            approved_by=None, approval_status="APPROVED", risk_score=0.2,
            risk_reason="reason", dispatch_status="PENDING", external_reference=None,
            approval_required=False, rejection_reason=None, approved_at=None,
            rejected_at=None, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )
        
        dummy_audit = AuditEventModel(
            id="audit_123", event_type="test", actor_id="user", actor_type="op",
            entity_type="entity", entity_id="123", metadata_fields={},
            created_at=datetime.now(timezone.utc)
        )
        
        dummy_webhook = WebhookDeliveryModel(
            id="del_123", repair_request_id="rep_123", webhook_url="url",
            delivery_status="SENT", status_code=200, error_message=None,
            payload_hash="abc", attempt_count=1, created_at=datetime.now(timezone.utc)
        )

        def execute_side_effect(stmt, *args, **kwargs):
            stmt_str = str(stmt).lower()
            res = MagicMock()
            if "bilgeapi_incidents" in stmt_str:
                res.scalar_one_or_none.return_value = dummy_incident
                res.scalars.return_value.all.return_value = [dummy_incident]
            elif "bilgeapi_diagnostic_runs" in stmt_str:
                res.scalar_one_or_none.return_value = dummy_diagnostic
                res.scalars.return_value.all.return_value = [dummy_diagnostic]
            elif "bilgeapi_findings" in stmt_str:
                res.scalar_one_or_none.return_value = dummy_finding
                res.scalars.return_value.all.return_value = [dummy_finding]
            elif "bilgeapi_recommendations" in stmt_str:
                res.scalar_one_or_none.return_value = dummy_recommendation
                res.scalars.return_value.all.return_value = [dummy_recommendation]
            elif "bilgeapi_repair_requests" in stmt_str:
                res.scalar_one_or_none.return_value = dummy_repair
                res.scalars.return_value.all.return_value = [dummy_repair]
            elif "bilgeapi_audit_events" in stmt_str:
                res.scalar_one_or_none.return_value = dummy_audit
                res.scalars.return_value.all.return_value = [dummy_audit]
            elif "bilgeapi_webhook_deliveries" in stmt_str:
                res.scalar_one_or_none.return_value = dummy_webhook
                res.scalars.return_value.all.return_value = [dummy_webhook]
            else:
                res.scalar_one_or_none.return_value = None
                res.scalars.return_value.all.return_value = []
            return res
        mock_db.execute.side_effect = execute_side_effect
        
        # Test Incident Repo
        inc_repo = PostgresIncidentRepository(mock_db)
        inc_data = IncidentCreate(
            project_key="proj", source_system="sys", environment="dev",
            kind="db", severity=Severity.HIGH, error_message="err",
            occurred_at=datetime.now(timezone.utc)
        )
        await inc_repo.create(inc_data)
        await inc_repo.get("inc_123")
        await inc_repo.list_all(project_key="proj")
        
        # Test Diagnostic Repo
        diag_repo = PostgresDiagnosticRepository(mock_db)
        from apps.bilgeapi.schemas.diagnostic import DiagnosticStatus
        await diag_repo.create("inc_123")
        await diag_repo.get("diag_123")
        await diag_repo.update("diag_123", status=DiagnosticStatus.COMPLETED, confidence=0.9)
        await diag_repo.list_all()
        
        # Test Finding Repo
        finding_repo = PostgresFindingRepository(mock_db)
        await finding_repo.create("diag_123", {"description": "finding-desc"})
        await finding_repo.list_by_diagnostic("diag_123")
        
        # Test Recommendation Repo
        rec_repo = PostgresRecommendationRepository(mock_db)
        await rec_repo.create("diag_123", {"description": "rec-desc", "action_code": "action-code"})
        await rec_repo.list_by_diagnostic("diag_123")
        
        # Test Repair Repo
        repair_repo = PostgresRepairRequestRepository(mock_db)
        repair_data = RepairRequestCreate(
            requested_by="user", risk_score=0.2, risk_reason="reason",
            approval_required=False, approval_status=ApprovalStatus.APPROVED
        )
        await repair_repo.create("diag_123", repair_data)
        await repair_repo.get("rep_123")
        await repair_repo.update("rep_123", approval_status=ApprovalStatus.APPROVED, dispatch_status=DispatchStatus.PENDING)
        await repair_repo.list_all()
        
        # Test Audit Repo
        audit_repo = PostgresAuditRepository(mock_db)
        from apps.bilgeapi.schemas.audit import AuditEvent
        dummy_event = AuditEvent(
            id="audit_123", event_type="test", actor_id="user", actor_type="op",
            entity_type="entity", entity_id="123", created_at=datetime.now(timezone.utc)
        )
        await audit_repo.write(dummy_event)
        await audit_repo.list_recent(limit=10)
        
        # Test Webhook Repo
        webhook_repo = PostgresWebhookDeliveryRepository(mock_db)
        await webhook_repo.create_delivery({"repair_request_id": "rep_123", "webhook_url": "url", "payload_hash": "abc"})
        await webhook_repo.update_delivery("del_123", "SENT", 200, "err", 1)
        await webhook_repo.list_deliveries()
 
    async def test_repairs_router_endpoints(self, test_client):
        # GET all repair requests (should return empty list initially)
        response = test_client.get("/v1/repair-requests")
        assert response.status_code == 200
        assert response.json() == []
 
        # POST /v1/webhooks/test
        response = test_client.post(
            "/v1/webhooks/test",
            json={"webhook_url": "https://8.8.8.8/dispatch", "payload": {"test": True}}
        )
        assert response.status_code == 200
        assert "signature" in response.json()

        from apps.bilgeapi.schemas.repair import ApprovalStatus, DispatchStatus, RepairRequestResponse
        from apps.bilgeapi.repositories.memory import memory_repositories
        
        repair_id = "rep_test_123"
        memory_repositories.repair_requests[repair_id] = RepairRequestResponse(
            id=repair_id,
            diagnostic_id="diag_123",
            requested_by="test-admin",
            approved_by=None,
            approval_status=ApprovalStatus.PENDING,
            risk_score=0.1,
            risk_reason="Low risk",
            dispatch_status=DispatchStatus.PENDING,
            external_reference=None,
            approval_required=True,
            rejection_reason=None,
            approved_at=None,
            rejected_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # GET /v1/repair-requests/{id}
        response = test_client.get(f"/v1/repair-requests/{repair_id}")
        assert response.status_code == 200
        assert response.json()["id"] == repair_id

        # POST /v1/repair-requests/{id}/approve
        response = test_client.post(f"/v1/repair-requests/{repair_id}/approve")
        assert response.status_code == 200
        assert response.json()["approval_status"] == ApprovalStatus.APPROVED

        # POST /v1/repair-requests/{id}/reject
        reject_id = "rep_reject_123"
        memory_repositories.repair_requests[reject_id] = memory_repositories.repair_requests[repair_id].model_copy(
            update={"id": reject_id, "approval_status": ApprovalStatus.PENDING}
        )
        
        response = test_client.post(
            f"/v1/repair-requests/{reject_id}/reject",
            json={"rejection_reason": "bad patch"}
        )
        assert response.status_code == 200
        assert response.json()["approval_status"] == ApprovalStatus.REJECTED

        # GET /v1/webhook-deliveries
        response = test_client.get("/v1/webhook-deliveries")
        assert response.status_code == 200

        # POST /v1/repair-requests/{id}/dispatch
        dispatch_id = "rep_dispatch_123"
        memory_repositories.repair_requests[dispatch_id] = memory_repositories.repair_requests[repair_id].model_copy(
            update={"id": dispatch_id, "approval_status": ApprovalStatus.APPROVED, "dispatch_status": DispatchStatus.PENDING}
        )

        response = test_client.post(
            f"/v1/repair-requests/{dispatch_id}/dispatch",
            json={"webhook_url": "https://8.8.8.8/dispatch"}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestReleaseGatePhase11:

    async def test_check_test_and_coverage_xml(self):
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        xml_content = """<?xml version="1.0" ?>
        <coverage line-rate="0.875" branch-rate="0.5">
            <sources><source>/path/to/project</source></sources>
        </coverage>
        """
        with patch("os.path.exists", side_effect=lambda p: p == "coverage.xml"):
            with patch("builtins.open", mock_open(read_data=xml_content)):
                # Mock ET.parse
                import xml.etree.ElementTree as ET
                mock_root = MagicMock()
                mock_root.attrib = {"line-rate": "0.875"}
                with patch("xml.etree.ElementTree.parse", return_value=MagicMock(getroot=lambda: mock_root)):
                    res = gate.check_test_and_coverage()
                    assert res["coverage_pct"] == 87.5
                    assert res["source"] == "coverage.xml"
                    assert len(res["blockers"]) == 0

    async def test_check_test_and_coverage_sqlite(self):
        import sys
        from unittest.mock import MagicMock
        
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        # Mock coverage package if not present in sys.modules
        if "coverage" not in sys.modules:
            mock_module = MagicMock()
            sys.modules["coverage"] = mock_module
        else:
            mock_module = sys.modules["coverage"]

        # Mock coverage package and load
        mock_cov = MagicMock()
        mock_cov.report.return_value = 82.34
        mock_module.Coverage.return_value = mock_cov
        
        with patch("os.path.exists", side_effect=lambda p: p == ".coverage"):
            with patch("coverage.Coverage", return_value=mock_cov):
                res = gate.check_test_and_coverage()
                assert res["coverage_pct"] == 82.34
                assert res["source"] == ".coverage"
                assert len(res["blockers"]) == 0


    async def test_check_test_and_coverage_txt(self):
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        txt_content = """
        TOTAL                                             2488    315    87%
        ====== 119 passed, 0 failed, 18 warnings in 19.58s =====
        """
        with patch("os.path.exists", side_effect=lambda p: p == "pytest_output.txt"):
            with patch("builtins.open", mock_open(read_data=txt_content)):
                res = gate.check_test_and_coverage()
                assert res["coverage_pct"] == 87.0
                assert res["source"] == "pytest_output.txt"
                assert res["passed_tests"] == 119
                assert res["failed_tests"] == 0
                assert len(res["blockers"]) == 0

    async def test_check_test_and_coverage_txt_with_failures(self):
        _clean_env()
        os.environ["APP_ENV"] = "production"
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        txt_content = """
        TOTAL                                             2488    315    87%
        ====== 2 failed, 117 passed, 18 warnings in 19.58s =====
        """
        with patch("os.path.exists", side_effect=lambda p: p == "pytest_output.txt"):
            with patch("builtins.open", mock_open(read_data=txt_content)):
                res = gate.check_test_and_coverage()
                assert res["coverage_pct"] == 87.0
                assert res["failed_tests"] == 2
                assert len(res["blockers"]) > 0

    async def test_check_test_and_coverage_missing_evidence(self):
        _clean_env()
        os.environ["APP_ENV"] = "production"
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        with patch("os.path.exists", return_value=False):
            res = gate.check_test_and_coverage()
            assert res["coverage_pct"] is None
            assert len(res["blockers"]) > 0
            assert "No test coverage evidence found" in res["blockers"][0]

    async def test_check_database_migrations_match(self):
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        mock_config = MagicMock()
        mock_script = MagicMock()
        mock_script.get_current_head.return_value = "rev123"

        # Mock DB session returning rev123
        mock_session = AsyncMock()
        mock_res = MagicMock()
        mock_res.fetchone.return_value = ["rev123"]
        mock_session.execute.return_value = mock_res
        
        mock_session_factory = AsyncMock()
        mock_session_factory.__aenter__.return_value = mock_session
        mock_session_local = MagicMock(return_value=mock_session_factory)

        with patch("os.path.exists", return_value=True):
            with patch("alembic.config.Config", return_value=mock_config):
                with patch("alembic.script.ScriptDirectory.from_config", return_value=mock_script):
                    with patch("libs.db.session.AsyncSessionLocal", mock_session_local):
                        res = await gate.check_database_migrations()
                        assert res["head_revision"] == "rev123"
                        assert res["current_revision"] == "rev123"
                        assert len(res["blockers"]) == 0

    async def test_check_database_migrations_mismatch_blocked(self):
        _clean_env()
        os.environ["APP_ENV"] = "production"
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        mock_config = MagicMock()
        mock_script = MagicMock()
        mock_script.get_current_head.return_value = "rev124"

        # Mock DB session returning rev123
        mock_session = AsyncMock()
        mock_res = MagicMock()
        mock_res.fetchone.return_value = ["rev123"]
        mock_session.execute.return_value = mock_res
        
        mock_session_factory = AsyncMock()
        mock_session_factory.__aenter__.return_value = mock_session
        mock_session_local = MagicMock(return_value=mock_session_factory)

        with patch("os.path.exists", return_value=True):
            with patch("alembic.config.Config", return_value=mock_config):
                with patch("alembic.script.ScriptDirectory.from_config", return_value=mock_script):
                    with patch("libs.db.session.AsyncSessionLocal", mock_session_local):
                        res = await gate.check_database_migrations()
                        assert res["head_revision"] == "rev124"
                        assert res["current_revision"] == "rev123"
                        assert len(res["blockers"]) > 0
                        assert "Database schema is not up to date" in res["blockers"][0]

    async def test_check_security_config_metrics_public_blocked_in_production(self):
        _clean_env()
        os.environ["APP_ENV"] = "production"
        settings.BILGEAPI_WEBHOOK_SECRET = "secure-webhook-secret-1234"
        settings.BILGEAPI_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_company"
        settings.BILGEAPI_CORS_ALLOWLIST = ["https://app.domain.com"]
        settings.BILGEAPI_AUTH_MODE = "api_key"
        settings.BILGEAPI_METRICS_PUBLIC = True  # Public in prod!

        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        res = gate.check_security_config()
        assert any("BILGEAPI_METRICS_PUBLIC" in b for b in res["blockers"])

    async def test_check_security_config_weak_secrets_blocked_in_production(self):
        _clean_env()
        os.environ["APP_ENV"] = "production"
        settings.BILGEAPI_WEBHOOK_SECRET = "short"  # Too short!
        settings.BILGEAPI_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_company"
        settings.BILGEAPI_CORS_ALLOWLIST = ["https://app.domain.com"]
        settings.BILGEAPI_AUTH_MODE = "jwt"
        settings.BILGEAPI_JWT_SECRET = "weak"  # Too short!
        settings.BILGEAPI_METRICS_PUBLIC = False

        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        res = gate.check_security_config()
        assert any("BILGEAPI_WEBHOOK_SECRET is too weak" in b for b in res["blockers"])
        assert any("BILGEAPI_JWT_SECRET is too weak" in b for b in res["blockers"])


from unittest.mock import mock_open


@pytest.mark.asyncio
class TestReleaseGateAgentShield:

    async def test_check_agentshield_security_clean(self):
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        mock_stdout = """{
            "findings": [],
            "score": {
                "grade": "A",
                "numericScore": 100
            }
        }"""
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_stdout, stderr="")
            res = gate.check_agentshield_security()
            assert res["score"] == 100.0
            assert res["grade"] == "A"
            assert res["findings_count"] == 0
            assert len(res["blockers"]) == 0
            assert len(res["warnings"]) == 0

    async def test_check_agentshield_security_with_findings(self):
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        mock_stdout = """{
            "findings": [
                {
                    "severity": "high",
                    "title": "Hook deletes files",
                    "file": "hooks/session-start.sh",
                    "line": 10
                },
                {
                    "severity": "low",
                    "title": "Unobserved skill",
                    "file": "skills/test.md",
                    "line": 1
                }
            ],
            "score": {
                "grade": "C",
                "numericScore": 75
            }
        }"""
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_stdout, stderr="")
            res = gate.check_agentshield_security()
            assert res["score"] == 75.0
            assert res["grade"] == "C"
            assert res["findings_count"] == 2
            assert len(res["blockers"]) == 1
            assert "AgentShield finding [HIGH]: Hook deletes files" in res["blockers"][0]
            assert len(res["warnings"]) == 1
            assert "AgentShield finding [LOW]: Unobserved skill" in res["warnings"][0]

    async def test_check_agentshield_security_failure_production(self):
        _clean_env()
        os.environ["APP_ENV"] = "production"
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="npx not found")
            res = gate.check_agentshield_security()
            assert len(res["blockers"]) == 1
            assert "AgentShield scanner failed to run" in res["blockers"][0]
            assert len(res["warnings"]) == 0

    async def test_check_agentshield_security_failure_development(self):
        _clean_env()
        os.environ["APP_ENV"] = "development"
        repo = InMemoryReleaseCheckRepository()
        gate = BilgeAPIReleaseGate(repo)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="npx not found")
            res = gate.check_agentshield_security()
            assert len(res["blockers"]) == 0
            assert len(res["warnings"]) == 1
            assert "AgentShield scanner failed to run" in res["warnings"][0]



