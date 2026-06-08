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
        "apps.bilgeapi.services.review_ledger",
        "apps.bilgeapi.models.database",
        "apps.bilgeapi.repositories.postgres",
        "apps.bilgeapi.repositories.memory",
        "apps.bilgeapi.routers.review_ledger",
        "apps.bilgeapi.schemas.review_ledger",
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
        "/v1/review-ledger/recent",
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
        elif len(webhook_secret) < 16:
            msg = "BILGEAPI_WEBHOOK_SECRET is too weak (must be at least 16 characters)."
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
        if settings.BILGEAPI_AUTH_MODE == "jwt":
            jwt_secret = settings.BILGEAPI_JWT_SECRET
            if not jwt_secret:
                msg = "BILGEAPI_JWT_SECRET is required when auth mode is 'jwt' in production."
                if is_production:
                    blockers.append(msg)
                else:
                    warnings.append(msg)
            elif len(jwt_secret) < 32:
                msg = "BILGEAPI_JWT_SECRET is too weak (must be at least 32 characters for HMAC-SHA256)."
                if is_production:
                    blockers.append(msg)
                else:
                    warnings.append(msg)

        # Static API Keys Check
        if settings.BILGEAPI_STATIC_KEYS:
            msg = "Plaintext BILGEAPI_STATIC_KEYS usage is discouraged. Use hashed API keys (BILGEAPI_STATIC_KEY_HASHES) instead."
            if is_production:
                blockers.append(msg)
            else:
                warnings.append(msg)

        if settings.BILGEAPI_AUTH_MODE in ("api_key", "hybrid", "disabled"):
            from apps.bilgeapi.auth import parse_static_keys
            try:
                keys = parse_static_keys()
                for key in keys:
                    if len(key) < 16 or key in ("dev-test-key-001", "dev-test-key-002", "test_key_1", "test_key_2"):
                        msg = f"Static API key '{key[:4]}...' is default or too weak (must be at least 16 characters)."
                        if is_production:
                            blockers.append(msg)
                        else:
                            warnings.append(msg)
            except Exception as e:
                logger.warning(f"Failed to check static key strength: {e}")

        # Redis Fallback Check
        try:
            import apps.bilgeapi.main as bilgeapi_main
            if getattr(bilgeapi_main, "REDIS_FALLBACK_ACTIVE", False):
                warnings.append("Redis rate limiter connection fallback is currently active (falling back to in-memory rate limiter).")
        except Exception:
            pass

        # Metrics Privacy Check
        if is_production and settings.BILGEAPI_METRICS_PUBLIC:
            blockers.append("BILGEAPI_METRICS_PUBLIC must be disabled (false) in production.")

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
                incident_repo=incident_repo,
                diagnostic_repo=diagnostic_repo,
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

    def check_test_and_coverage(self) -> Dict[str, Any]:
        """
        Phase 11: Reads existing test and coverage evidence files in read-only mode.
        Checks coverage.xml -> .coverage -> pytest_output.txt.
        """
        import re
        blockers = []
        warnings = []
        coverage_pct = None
        failed_tests = 0
        passed_tests = 0
        source = "NONE"

        is_production = settings.APP_ENV == "production"

        # 1. Try coverage.xml
        if os.path.exists("coverage.xml"):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse("coverage.xml")
                root = tree.getroot()
                line_rate = root.attrib.get("line-rate")
                if line_rate:
                    coverage_pct = float(line_rate) * 100.0
                    source = "coverage.xml"
            except Exception as e:
                logger.warning(f"Failed to parse coverage.xml: {e}")

        # 2. Try .coverage SQLite db
        if coverage_pct is None and os.path.exists(".coverage"):
            try:
                import coverage
                cov = coverage.Coverage(data_file=".coverage")
                cov.load()
                import io
                f = io.StringIO()
                coverage_pct = cov.report(file=f)
                source = ".coverage"
            except Exception as e:
                logger.warning(f"Failed to read .coverage database: {e}")

        # 3. Try pytest_output.txt or pytest_output_v10.txt etc.
        txt_files = ["pytest_output.txt", "pytest_output_v10.txt", "pytest_output_v11.txt", "pytest_output_v12.txt"]
        for txt_file in txt_files:
            if coverage_pct is None and os.path.exists(txt_file):
                try:
                    with open(txt_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    cov_match = re.search(r"Total coverage:\s*(\d+(?:\.\d+)?)%", content)
                    if not cov_match:
                        cov_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", content)
                    if cov_match:
                        coverage_pct = float(cov_match.group(1))
                        source = txt_file

                    fail_match = re.search(r"(\d+)\s+failed", content)
                    if fail_match:
                        failed_tests = int(fail_match.group(1))
                    pass_match = re.search(r"(\d+)\s+passed", content)
                    if pass_match:
                        passed_tests = int(pass_match.group(1))
                except Exception as e:
                    logger.warning(f"Failed to parse {txt_file}: {e}")

        # Check constraints
        if coverage_pct is None:
            msg = "No test coverage evidence found (coverage.xml, .coverage, or pytest_output.txt missing)."
            if is_production:
                blockers.append(msg)
            else:
                warnings.append(msg)
        else:
            min_cov = settings.BILGEAPI_RELEASE_MIN_COVERAGE
            if coverage_pct < min_cov:
                msg = f"Test coverage ({coverage_pct:.2f}%) is below minimum required threshold ({min_cov:.2f}%)."
                if is_production:
                    blockers.append(msg)
                else:
                    warnings.append(msg)

        if failed_tests > 0:
            msg = f"Test suite has {failed_tests} failed tests. Release blocked."
            if is_production:
                blockers.append(msg)
            else:
                warnings.append(msg)

        return {
            "coverage_pct": coverage_pct,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "source": source,
            "blockers": blockers,
            "warnings": warnings,
        }

    async def check_database_migrations(self) -> Dict[str, Any]:
        """
        Phase 11: Compares current DB revision with head migration using Alembic APIs in read-only mode.
        """
        blockers = []
        warnings = []
        head_rev = None
        current_rev = None
        is_production = settings.APP_ENV == "production"

        try:
            ini_path = "alembic.ini"
            if not os.path.exists(ini_path):
                ini_path = "libs/db/migrations/alembic.ini"

            if os.path.exists(ini_path):
                from alembic.config import Config
                from alembic.script import ScriptDirectory
                config = Config(ini_path)
                script = ScriptDirectory.from_config(config)
                head_rev = script.get_current_head()
            else:
                warnings.append("Alembic configuration (alembic.ini) not found.")
        except Exception as e:
            logger.warning(f"Failed to determine Alembic head revision: {e}")
            warnings.append(f"Alembic head check failed: {str(e)}")

        try:
            from libs.db.session import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                res = await session.execute(text("SELECT version_num FROM alembic_version"))
                row = res.fetchone()
                current_rev = row[0] if row else None
        except Exception as e:
            logger.warning(f"Failed to query alembic_version table: {e}")
            current_rev = None

        if head_rev:
            if current_rev != head_rev:
                msg = f"Database schema is not up to date. Head migration: {head_rev}, Current DB migration: {current_rev}"
                if is_production:
                    blockers.append(msg)
                else:
                    warnings.append(msg)
        else:
            msg = "Could not verify Alembic head revision."
            if is_production:
                blockers.append(msg)
            else:
                warnings.append(msg)

        return {
            "head_revision": head_rev,
            "current_revision": current_rev,
            "blockers": blockers,
            "warnings": warnings,
        }

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
        blockers = list(security_res["blockers"])
        warnings = list(security_res["warnings"])

        # 4. E2E dry-run simulation
        smoke_trace = await self.run_e2e_dry_run()
        dry_run_failed = any(step["status"] == "FAILED" for step in smoke_trace)

        if dry_run_failed:
            blockers.append("E2E Dry-run smoke test failed during pipeline simulation.")

        if missing_modules:
            blockers.append(f"Module check failed for: {', '.join(missing_modules)}")

        # 5. Check Test and Coverage Evidence (Phase 11)
        coverage_res = self.check_test_and_coverage()
        blockers.extend(coverage_res["blockers"])
        warnings.extend(coverage_res["warnings"])

        smoke_trace.append({
            "step": 7,
            "action": "TEST_AND_COVERAGE_CHECK",
            "status": "PASSED" if not coverage_res["blockers"] else "FAILED",
            "details": f"Source: {coverage_res['source']}, Coverage: {coverage_res['coverage_pct']}%, Passed: {coverage_res['passed_tests']}, Failed: {coverage_res['failed_tests']}"
        })

        # 6. Check Database Migrations (Phase 11)
        migration_res = await self.check_database_migrations()
        blockers.extend(migration_res["blockers"])
        warnings.extend(migration_res["warnings"])

        smoke_trace.append({
            "step": 8,
            "action": "DATABASE_MIGRATION_CHECK",
            "status": "PASSED" if not migration_res["blockers"] else "FAILED",
            "details": f"Head Revision: {migration_res['head_revision']}, Current DB Revision: {migration_res['current_revision']}"
        })

        # 7. Scoring Algorithm
        score = 100.0
        score -= len(warnings) * 5.0
        score -= len(blockers) * 20.0
        score = max(0.0, score)

        # 8. GO / NO-GO Decision Logic
        if blockers or score < 80:
            status = "BLOCKED"
        elif warnings or score < 90:
            status = "WARNING"
        else:
            status = "PASSED"

        # Gather metadata
        git_sha = os.getenv("BILGEAPI_GIT_SHA", os.getenv("GIT_SHA", "unknown"))
        app_version = "1.0.0"
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
