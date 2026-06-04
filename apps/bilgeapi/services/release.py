import asyncio
import importlib
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from apps.bilgeapi.config import settings
from apps.bilgeapi.repositories.interface import ReleaseCheckRepository
from apps.bilgeapi.schemas.repair import ApprovalStatus, DispatchStatus

logger = logging.getLogger("bilgeapi.release_gate")

class BilgeAPIReleaseGate:
    """
    Phase 8: Evaluates BilgeAPI against production readiness and security standards.
    """

    REQUIRED_MODULES = [
        "apps.bilgeapi.config",
        "apps.bilgeapi.auth",
        "apps.bilgeapi.startup",
        "apps.bilgeapi.main",
        "apps.bilgeapi.adapters.webhook",
        "apps.bilgeapi.services.risk",
        "apps.bilgeapi.services.webhook",
        "apps.bilgeapi.services.audit",
        "apps.bilgeapi.services.diagnostic",
        "apps.bilgeapi.models.database",
        "apps.bilgeapi.repositories.postgres",
        "apps.bilgeapi.repositories.memory",
    ]

    REQUIRED_ENDPOINTS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/v1/catalog",
        "/v1/incidents",
        "/v1/diagnostics",
        "/v1/repair-requests",
        "/v1/audit-events",
        "/v1/webhook-deliveries",
    ]

    def __init__(self, repo: ReleaseCheckRepository):
        self.repo = repo

    def check_modules(self) -> Dict[str, str]:
        """Verifies core modules exist and can be imported."""
        results = {}
        for mod in self.REQUIRED_MODULES:
            try:
                importlib.import_module(mod)
                results[mod] = "OK"
            except Exception as e:
                logger.warning(f"Release Gate: Module verification failed for {mod}: {e}")
                results[mod] = f"ERROR: {str(e)}"
        return results

    def check_endpoints(self, app: FastAPI) -> Dict[str, str]:
        """Dinamik olarak FastAPI route tablosunu tarayarak core endpoint'lerin varlığını denetler."""
        results = {}
        registered_paths = {getattr(route, "path", "") for route in app.routes}
        for ep in self.REQUIRED_ENDPOINTS:
            if ep in registered_paths:
                results[ep] = "VERIFIED_PRESENT"
            else:
                logger.warning(f"Release Gate: Crucial endpoint missing: {ep}")
                results[ep] = "MISSING"
        return results

    def check_security_config(self) -> Dict[str, Any]:
        """Taramalar: production ortamında wildcard CORS, bypass vb. risklerin varlığını denetler."""
        blockers = []
        warnings = []

        is_production = settings.APP_ENV == "production"

        # Webhook Secret Check
        webhook_secret = os.getenv("BILGEAPI_WEBHOOK_SECRET", "webhook_secret")
        if not webhook_secret or webhook_secret == "webhook_secret":
            msg = "BILGEAPI_WEBHOOK_SECRET is missing or set to default."
            if is_production:
                blockers.append(msg)
            else:
                warnings.append(msg)

        # CORS wildcard check
        cors_raw = os.getenv("BILGEAPI_CORS_ALLOWLIST", "")
        if is_production and (not cors_raw or cors_raw.strip() == "*"):
            blockers.append("BILGEAPI_CORS_ALLOWLIST cannot be empty or '*' in production.")

        # Private webhook bypass in production check
        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if is_production and allow_private:
            blockers.append("BILGEAPI_ALLOW_PRIVATE_WEBHOOKS must be disabled in production.")

        # Database URL Check
        db_url = settings.BILGEAPI_DATABASE_URL
        if not db_url:
            db_url = settings.DATABASE_URL
        if is_production and (not db_url or "sqlite" in db_url or "localhost" in db_url or "127.0.0.1" in db_url):
            blockers.append("Production database URL must point to a real Postgres instance, not SQLite/localhost.")

        # Auth Mode Check
        if is_production and settings.BILGEAPI_AUTH_MODE == "disabled":
            blockers.append("BILGEAPI_AUTH_MODE cannot be 'disabled' in production.")

        # JWT Secret Check
        if is_production and settings.BILGEAPI_AUTH_MODE == "jwt" and not settings.BILGEAPI_JWT_SECRET:
            blockers.append("BILGEAPI_JWT_SECRET is required when auth mode is 'jwt' in production.")

        return {
            "blockers": blockers,
            "warnings": warnings,
            "security_hardened": len(blockers) == 0
        }

    async def run_e2e_dry_run(self, dispatcher: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Runs an isolated, simulated E2E dry-run of the intake -> diagnostic -> repair -> dispatch flow.
        Uses memory repositories to guarantee zero database mutation or code/patch side-effects.
        Fully mocks outgoing webhook HTTP calls to ensure zero outbound traffic during gate audit.
        """
        trace = []
        try:
            # 1. Setup in-memory repos and services
            from apps.bilgeapi.repositories.memory import (
                InMemoryIncidentRepository,
                InMemoryDiagnosticRepository,
                InMemoryFindingRepository,
                InMemoryRecommendationRepository,
                InMemoryRepairRequestRepository,
                InMemoryAuditRepository,
                InMemoryWebhookDeliveryRepository
            )
            from apps.bilgeapi.services.diagnostic import DiagnosticService
            from apps.bilgeapi.services.webhook import WebhookDeliveryService
            from apps.bilgeapi.services.audit import AuditService
            from apps.bilgeapi.services.risk import RiskScoringService
            from apps.bilgeapi.schemas.incident import IncidentCreate, Severity

            incident_repo = InMemoryIncidentRepository()
            diagnostic_repo = InMemoryDiagnosticRepository()
            finding_repo = InMemoryFindingRepository()
            recommendation_repo = InMemoryRecommendationRepository()
            repair_repo = InMemoryRepairRequestRepository()
            audit_repo = InMemoryAuditRepository()
            webhook_repo = InMemoryWebhookDeliveryRepository()

            audit_service = AuditService(audit_repo)
            diagnostic_service = DiagnosticService(
                incident_repo=incident_repo,
                diagnostic_repo=diagnostic_repo,
                finding_repo=finding_repo,
                recommendation_repo=recommendation_repo,
                audit_service=audit_service
            )
            risk_scoring_service = RiskScoringService()

            # Set up mock dispatcher if not provided
            if dispatcher is None:
                mock_dispatcher = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_dispatcher.dispatch.return_value = mock_response
                dispatcher = mock_dispatcher

            webhook_service = WebhookDeliveryService(
                webhook_repo=webhook_repo,
                repair_repo=repair_repo,
                audit_service=audit_service,
                dispatcher=dispatcher
            )

            # Step 1: Create Incident
            inc_data = IncidentCreate(
                project_key="smoke-proj",
                source_system="release-gate-dry-run",
                environment="test",
                kind="CRITICAL_DB_LAG",
                severity=Severity.HIGH,
                error_message="Simulated DB latency threshold exceeded",
                occurred_at=datetime.now(timezone.utc),
                correlation_id="corr-dry-run-001"
            )
            incident = await incident_repo.create(inc_data)
            trace.append({
                "step": 1,
                "action": "INCIDENT_INTAKE",
                "status": "PASSED",
                "details": f"Incident registered in isolated memory repo. ID: {incident.id}"
            })

            # Step 2: Trigger Diagnostic Run
            diag_run = await diagnostic_service.start_diagnostic(incident.id)
            trace.append({
                "step": 2,
                "action": "DIAGNOSTIC_RUN_INITIATE",
                "status": "PASSED",
                "details": f"Diagnostic run created. ID: {diag_run.diagnostic_id}"
            })

            # Step 3: Wait for diagnostic background run to finish evaluating
            await asyncio.sleep(0.1)
            diagnostic = await diagnostic_repo.get(diag_run.diagnostic_id)
            findings = await finding_repo.list_by_diagnostic(diag_run.diagnostic_id)
            recommendations = await recommendation_repo.list_by_diagnostic(diag_run.diagnostic_id)
            trace.append({
                "step": 3,
                "action": "DIAGNOSTIC_EVALUATION",
                "status": "PASSED",
                "details": f"Generated {len(findings)} findings and {len(recommendations)} recommendations. Status: {diagnostic.status}"
            })

            # Step 4: Calculate Risk Score
            risk_score, risk_reason = risk_scoring_service.calculate_risk(incident, diagnostic)
            is_low_risk = risk_score < 0.3
            is_prod = incident.environment.lower() == "production"
            is_sensitive = ("security" in risk_reason.lower() or 
                            "database" in risk_reason.lower() or 
                            "workflow" in risk_reason.lower())

            approval_required = not (is_low_risk and not is_prod and not is_sensitive)
            risk_level = "HIGH" if risk_score >= 0.7 else "MEDIUM" if risk_score >= 0.3 else "LOW"

            trace.append({
                "step": 4,
                "action": "RISK_SCORING",
                "status": "PASSED",
                "details": f"Risk evaluation: Score={risk_score}, Level={risk_level}"
            })

            # Step 5: Prepare Repair Request
            from apps.bilgeapi.schemas.repair import RepairRequestCreate
            
            # Apply auto-approval logic
            if not approval_required:
                approval_status = ApprovalStatus.APPROVED
                approved_by = "system"
                approved_at = datetime.now(timezone.utc)
                status_msg = "Auto-approved due to low risk profile."
            else:
                approval_status = ApprovalStatus.PENDING
                approved_by = None
                approved_at = None
                status_msg = "Awaiting manual operator signoff."

            repair_data = RepairRequestCreate(
                requested_by="release-gate",
                risk_score=risk_score,
                risk_reason=risk_reason,
                approval_required=approval_required,
                approval_status=approval_status,
                approved_by=approved_by,
                approved_at=approved_at
            )
            repair_request = await repair_repo.create(diagnostic.diagnostic_id, repair_data)
            
            # Apply update to repository state if auto-approved
            if not approval_required:
                repair_request = await repair_repo.update(
                    repair_request_id=repair_request.id,
                    approval_status=ApprovalStatus.APPROVED,
                    dispatch_status=DispatchStatus.PENDING
                )

            trace.append({
                "step": 5,
                "action": "REPAIR_REQUEST_PREPARATION",
                "status": "PASSED",
                "details": f"Repair request ID: {repair_request.id}. Status: {repair_request.approval_status}. {status_msg}"
            })

            # Step 6: Simulate Webhook Dispatch
            webhook_url = "https://8.8.8.8/dispatch"

            # Ensure it's approved first to run dispatch
            if repair_request.approval_status != ApprovalStatus.APPROVED:
                repair_request = await repair_repo.update(
                    repair_request_id=repair_request.id,
                    approval_status=ApprovalStatus.APPROVED,
                    dispatch_status=DispatchStatus.PENDING
                )
            
            dispatch_payload = {"repair_request_id": repair_request.id, "dry_run": True}
            await webhook_service.dispatch_webhook(
                repair_request_id=repair_request.id,
                webhook_url=webhook_url,
                payload=dispatch_payload
            )
            
            # Give background task brief moment to run inside event loop
            await asyncio.sleep(0.05)

            deliveries = await webhook_repo.list_deliveries()
            if deliveries:
                delivery = deliveries[0]
                trace.append({
                    "step": 6,
                    "action": "WEBHOOK_DISPATCH_SIMULATION",
                    "status": "PASSED",
                    "details": f"Webhook mock delivery registered (Attempt={delivery['attempt_count']}, Status={delivery['delivery_status']})"
                })
            else:
                trace.append({
                    "step": 6,
                    "action": "WEBHOOK_DISPATCH_SIMULATION",
                    "status": "WARNING",
                    "details": "Webhook delivery not persisted in memory repository."
                })

        except Exception as e:
            logger.error(f"Release Gate E2E Dry-run failed: {e}")
            trace.append({
                "step": len(trace) + 1,
                "action": "DRY_RUN_FATAL_ERROR",
                "status": "FAILED",
                "details": f"Dry-run failed: {str(e)}"
            })
        return trace

    async def execute_readiness_audit(self, triggered_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs the full readiness check pipeline and persists results into DB/repository.
        Calculates release readiness scorecard & score.
        """
        # 1. Check modules
        modules_res = self.check_modules()
        missing_modules = [m for m, stat in modules_res.items() if "ERROR" in stat]

        # 2. Check endpoints
        # Note: app must be provided, to be done by the router injection.
        # But we will calculate it in the router handler.
        
        # 3. Security Config Check
        security_res = self.check_security_config()
        blockers = security_res["blockers"]
        warnings = security_res["warnings"]

        # 4. E2E dry-run simulation
        smoke_trace = await self.run_e2e_dry_run()
        dry_run_failed = any(step["status"] == "FAILED" for step in smoke_trace)

        if dry_run_failed:
            blockers.append("E2E Dry-run smoke test failed during pipeline simulation.")

        if missing_modules:
            blockers.append(f"Module check failed for: {', '.join(missing_modules)}")

        # 5. Scoring Algorithm
        score = 100.0
        score -= len(warnings) * 5.0
        score -= len(blockers) * 20.0
        score = max(0.0, score)

        # 6. GO / NO-GO Decision Logic
        if blockers or score < 80:
            status = "BLOCKED"
        elif warnings or score < 90:
            status = "WARNING"
        else:
            status = "PASSED"

        # Gather metadata
        git_sha = os.getenv("BILGEAPI_GIT_SHA", os.getenv("GIT_SHA", "unknown"))
        app_version = "1.0.0-phase8"
        environment = settings.APP_ENV

        check_data = {
            "status": status,
            "score": score,
            "blockers": blockers,
            "warnings": warnings,
            "checked_modules": modules_res,
            "checked_endpoints": {},  # Will be populated by the caller (router)
            "smoke_trace": smoke_trace,
            "app_version": app_version,
            "git_sha": git_sha,
            "environment": environment,
            "triggered_by": triggered_by
        }
        return check_data
