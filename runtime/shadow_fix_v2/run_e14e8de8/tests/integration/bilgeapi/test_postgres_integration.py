import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from libs.db.base import Base
from apps.bilgeapi.models.database import (
    IncidentModel, DiagnosticRunModel, FindingModel, RecommendationModel,
    RepairRequestModel, AuditEventModel, WebhookDeliveryModel,
    PrReviewFeedbackModel, PatchRevisionModel, PrVerificationModel, PrDraftModel, ImprovementProposalModel
)
from apps.bilgeapi.schemas.incident import IncidentCreate, Severity
from apps.bilgeapi.schemas.diagnostic import DiagnosticStatus
from apps.bilgeapi.schemas.repair import RepairRequestCreate, ApprovalStatus, DispatchStatus
from apps.bilgeapi.schemas.audit import AuditEvent
from apps.bilgeapi.repositories.postgres import (
    PostgresIncidentRepository,
    PostgresDiagnosticRepository,
    PostgresFindingRepository,
    PostgresRecommendationRepository,
    PostgresRepairRequestRepository,
    PostgresAuditRepository,
    PostgresWebhookDeliveryRepository,
    PostgresPrReviewFeedbackRepository,
    PostgresPatchRevisionRepository,
    PostgresPrVerificationRepository,
    PostgresPrDraftRepository,
    PostgresImprovementRepository,
    PostgresResearchRepository,
    PostgresSystemFindingRepository,
    PostgresRemediationRunbookRepository,
    PostgresRemediationAttemptRepository
)

@pytest.mark.asyncio
async def test_postgres_repositories_integration():
    # Create isolated in-memory SQLite async engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # Create the tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Instantiate repositories
        incident_repo = PostgresIncidentRepository(session)
        diagnostic_repo = PostgresDiagnosticRepository(session)
        finding_repo = PostgresFindingRepository(session)
        recommendation_repo = PostgresRecommendationRepository(session)
        repair_repo = PostgresRepairRequestRepository(session)
        audit_repo = PostgresAuditRepository(session)
        webhook_repo = PostgresWebhookDeliveryRepository(session)
        
        # 1. Test Incident Repository
        incident_create = IncidentCreate(
            project_key="test-project",
            source_system="test-source",
            environment="testing",
            kind="integration",
            severity=Severity.HIGH,
            error_message="Test error message",
            stack_trace="Test stack trace",
            occurred_at=datetime.now(timezone.utc),
            correlation_id="corr-123",
            tags=["test", "integration"],
            metadata={"region": "us-east-1"}
        )
        
        created_incident = await incident_repo.create(incident_create)
        assert created_incident.id.startswith("inc_")
        assert created_incident.project_key == "test-project"
        assert created_incident.correlation_id == "corr-123"
        assert created_incident.tags == ["test", "integration"]
        
        fetched_incident = await incident_repo.get(created_incident.id)
        assert fetched_incident is not None
        assert fetched_incident.id == created_incident.id
        
        all_incidents = await incident_repo.list_all(project_key="test-project")
        assert len(all_incidents) == 1
        assert all_incidents[0].id == created_incident.id
        
        # 2. Test Diagnostic Repository
        diag_run = await diagnostic_repo.create(created_incident.id)
        assert diag_run.diagnostic_id.startswith("diag_")
        assert diag_run.status == DiagnosticStatus.QUEUED.value
        
        fetched_diag = await diagnostic_repo.get(diag_run.diagnostic_id)
        assert fetched_diag is not None
        assert fetched_diag.diagnostic_id == diag_run.diagnostic_id
        
        updated_diag = await diagnostic_repo.update(
            diag_run.diagnostic_id,
            status=DiagnosticStatus.RUNNING,
            summary="Running diagnostic checks",
            root_cause_hypothesis="Hypothesis X",
            confidence=0.85,
            risk_score=0.4
        )
        assert updated_diag.status == DiagnosticStatus.RUNNING.value
        assert updated_diag.summary == "Running diagnostic checks"
        assert updated_diag.confidence == 0.85
        
        # 3. Test Finding Repository
        finding_data = {
            "description": "Found anomaly in log files",
            "log_line_number": 42
        }
        finding = await finding_repo.create(diag_run.diagnostic_id, finding_data)
        assert finding["id"].startswith("find_")
        assert finding["description"] == "Found anomaly in log files"
        assert finding["metadata"] == {"log_line_number": 42}
        
        findings = await finding_repo.list_by_diagnostic(diag_run.diagnostic_id)
        assert len(findings) == 1
        assert findings[0]["id"] == finding["id"]
        
        # 4. Test Recommendation Repository
        rec_data = {
            "description": "Restart the database container",
            "priority": "HIGH"
        }
        recommendation = await recommendation_repo.create(diag_run.diagnostic_id, rec_data)
        assert recommendation["id"].startswith("rec_")
        assert recommendation["description"] == "Restart the database container"
        assert recommendation["metadata"] == {"priority": "HIGH"}
        
        recommendations = await recommendation_repo.list_by_diagnostic(diag_run.diagnostic_id)
        assert len(recommendations) == 1
        assert recommendations[0]["id"] == recommendation["id"]
        
        # Verify get diagnostic includes findings & recommendations
        refetched_diag = await diagnostic_repo.get(diag_run.diagnostic_id)
        assert len(refetched_diag.findings) == 1
        assert len(refetched_diag.recommendations) == 1
        assert refetched_diag.findings[0]["description"] == "Found anomaly in log files"
        assert refetched_diag.recommendations[0]["description"] == "Restart the database container"
        
        # 5. Test Repair Request Repository
        repair_create = RepairRequestCreate(
            requested_by="admin",
            risk_score=0.4,
            risk_reason="Low risk restart"
        )
        repair_req = await repair_repo.create(diag_run.diagnostic_id, repair_create)
        assert repair_req.id.startswith("rep_")
        assert repair_req.requested_by == "admin"
        assert repair_req.approval_status == ApprovalStatus.PENDING.value
        assert repair_req.dispatch_status == DispatchStatus.PENDING.value
        
        fetched_repair = await repair_repo.get(repair_req.id)
        assert fetched_repair is not None
        assert fetched_repair.id == repair_req.id
        
        updated_repair = await repair_repo.update(
            repair_req.id,
            approval_status=ApprovalStatus.APPROVED,
            dispatch_status=DispatchStatus.DISPATCHED,
            approved_by="operator-1",
            external_reference="ext-ref-abc"
        )
        assert updated_repair.approval_status == ApprovalStatus.APPROVED.value
        assert updated_repair.dispatch_status == DispatchStatus.DISPATCHED.value
        assert updated_repair.approved_by == "operator-1"
        assert updated_repair.external_reference == "ext-ref-abc"
        
        all_repairs = await repair_repo.list_all()
        assert len(all_repairs) == 1
        assert all_repairs[0].id == repair_req.id
        
        # 6. Test Audit Repository
        audit_event = AuditEvent(
            id="audit-1",
            event_type="INCIDENT_CREATED",
            actor_id="system",
            actor_type="service",
            entity_type="incident",
            entity_id=created_incident.id,
            request_id="req-999",
            correlation_id="corr-123",
            ip_address="127.0.0.1",
            user_agent="pytest",
            before_state=None,
            after_state={"id": created_incident.id},
            metadata={"source": "pytest"},
            created_at=datetime.now(timezone.utc)
        )
        await audit_repo.write(audit_event)
        
        recent_audits = await audit_repo.list_recent(limit=10)
        assert len(recent_audits) >= 1
        assert any(e.id == "audit-1" for e in recent_audits)
        
        # 7. Test Webhook Delivery Repository
        delivery_data = {
            "repair_request_id": repair_req.id,
            "webhook_url": "https://example.com/webhook",
            "status_code": 200,
            "delivery_status": "success",
            "error_message": None,
            "payload_hash": "hash123",
            "attempt_count": 1.0
        }
        await webhook_repo.log_delivery(delivery_data)
        
        # Webhook delivery model verify directly via select query in session
        res = await session.execute(select(WebhookDeliveryModel).where(WebhookDeliveryModel.repair_request_id == repair_req.id))
        webhook_model = res.scalar_one_or_none()
        assert webhook_model is not None
        assert webhook_model.webhook_url == "https://example.com/webhook"
        assert webhook_model.status_code == 200
        
    await engine.dispose()


@pytest.mark.asyncio
async def test_postgres_repositories_edge_cases():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        incident_repo = PostgresIncidentRepository(session)
        diagnostic_repo = PostgresDiagnosticRepository(session)
        repair_repo = PostgresRepairRequestRepository(session)
        
        # Test gets returning None
        assert await incident_repo.get("non-existent") is None
        assert await diagnostic_repo.get("non-existent") is None
        assert await diagnostic_repo.update("non-existent", DiagnosticStatus.RUNNING) is None
        assert await repair_repo.get("non-existent") is None
        assert await repair_repo.update("non-existent", ApprovalStatus.APPROVED, DispatchStatus.DISPATCHED) is None
        
        # Test update with list logic/completed time
        incident_create = IncidentCreate(
            project_key="proj-1",
            source_system="test-source",
            environment="testing",
            kind="integration",
            severity=Severity.HIGH,
            error_message="Test message",
            occurred_at=datetime.now(timezone.utc),
            correlation_id="corr-123"
        )
        created_inc = await incident_repo.create(incident_create)
        diag_run = await diagnostic_repo.create(created_inc.id)
        
        # Test updating with completed state and ignored kwargs (findings/recommendations)
        updated_diag = await diagnostic_repo.update(
            diag_run.diagnostic_id,
            status=DiagnosticStatus.COMPLETED,
            findings=[],
            recommendations=[],
            summary="Updated summary"
        )
        assert updated_diag.status == DiagnosticStatus.COMPLETED.value
        assert updated_diag.completed_at is not None
        
        # Test list_all for diagnostic runs
        all_diags = await diagnostic_repo.list_all()
        assert len(all_diags) == 1
        assert all_diags[0].diagnostic_id == diag_run.diagnostic_id
        
    await engine.dispose()


@pytest.mark.asyncio
async def test_postgres_feedback_and_revisions_integration():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        feedback_repo = PostgresPrReviewFeedbackRepository(session)
        revision_repo = PostgresPatchRevisionRepository(session)
        verification_repo = PostgresPrVerificationRepository(session)
        draft_repo = PostgresPrDraftRepository(session)
        proposal_repo = PostgresImprovementRepository(session)
        research_repo = PostgresResearchRepository(session)
        
        # Create Research Request
        research_data = {
            "incident_id": "inc_123",
            "query": "Fix memory leaks",
            "status": "COMPLETED",
            "tenant_id": "test_tenant"
        }
        research = await research_repo.create_request(research_data)
        
        # 1. Setup Proposal and PR Draft
        proposal_data = {
            "research_id": research["id"],
            "title": "Clean memory leaks",
            "rationale": "leaks",
            "status": "APPROVED",
            "patch_code": "diff --git a/main.py b/main.py",
            "gate_status": "GATE_PASSED"
        }
        proposal = await proposal_repo.create_proposal(proposal_data)
        
        draft_data = {
            "proposal_id": proposal["id"],
            "provider": "github",
            "title": "Optimizing memory usage",
            "body": "closes memory leak",
            "risk_level": "LOW",
            "status": "DRAFT"
        }
        draft = await draft_repo.create_pr_draft(draft_data)
        
        # 2. Test Feedback Repository
        fb_data = {
            "pr_draft_id": draft["id"],
            "reviewer_id": "reviewer_1",
            "comment": "Rename variable `x` to `y`",
            "status": "PENDING"
        }
        created_fb = await feedback_repo.create_feedback(fb_data)
        assert created_fb["id"].startswith("pfb_")
        assert created_fb["comment"] == "Rename variable `x` to `y`"
        assert created_fb["status"] == "PENDING"
        
        fetched_fb = await feedback_repo.get_feedback(created_fb["id"])
        assert fetched_fb is not None
        assert fetched_fb["id"] == created_fb["id"]
        
        all_feedbacks = await feedback_repo.list_feedback_by_pr_draft(draft["id"])
        assert len(all_feedbacks) == 1
        assert all_feedbacks[0]["id"] == created_fb["id"]
        
        updated_fb = await feedback_repo.update_feedback_status(created_fb["id"], "RESOLVED")
        assert updated_fb["status"] == "RESOLVED"
        
        # 3. Test Patch Revision Repository
        rev_data = {
            "pr_draft_id": draft["id"],
            "feedback_id": created_fb["id"],
            "revision_number": 1,
            "revised_patch_code": "diff --git a/main.py b/main.py\n+y = 10",
            "risk_analysis": {"affected_files": ["main.py"]},
            "risk_level": "LOW",
            "verification_status": "PENDING",
            "created_by": "admin"
        }
        created_rev = await revision_repo.create_revision(rev_data)
        assert created_rev["id"].startswith("prev_")
        assert created_rev["revision_number"] == 1
        assert created_rev["risk_level"] == "LOW"
        
        fetched_rev = await revision_repo.get_revision(created_rev["id"])
        assert fetched_rev is not None
        assert fetched_rev["id"] == created_rev["id"]
        
        latest_num = await revision_repo.get_latest_revision_number(draft["id"])
        assert latest_num == 1
        
        all_revisions = await revision_repo.list_revisions_by_pr_draft(draft["id"])
        assert len(all_revisions) == 1
        assert all_revisions[0]["id"] == created_rev["id"]
        
        updated_rev = await revision_repo.update_verification_status(created_rev["id"], "VERIFIED")
        assert updated_rev["verification_status"] == "VERIFIED"
        
        # 4. Test Verification Repository with revision_id
        verification_data = {
            "pr_draft_id": draft["id"],
            "proposal_id": proposal["id"],
            "revision_id": created_rev["id"],
            "status": "REVIEW_READY",
            "review_score": 95.0,
            "review_decision": "REVIEW_READY",
            "risk_level": "LOW",
            "risk_flags": [],
            "affected_files": ["main.py"],
            "mutation_detected": False,
            "test_files_present": False,
            "patch_size_lines": 1,
            "test_plan": ["Run tests"],
            "rollback_plan": "checkout main",
            "verification_report": "All looks good"
        }
        verification = await verification_repo.create_verification(verification_data)
        assert verification["id"].startswith("prv_")
        assert verification["revision_id"] == created_rev["id"]
        
        fetched_verification = await verification_repo.get_verification_by_revision(created_rev["id"])
        assert fetched_verification is not None
        assert fetched_verification["id"] == verification["id"]
        
        # Edge cases: gets returning None
        assert await feedback_repo.get_feedback("non-existent") is None
        assert await feedback_repo.update_feedback_status("non-existent", "RESOLVED") is None
        assert await revision_repo.get_revision("non-existent") is None
        assert await revision_repo.update_verification_status("non-existent", "VERIFIED") is None
        
    await engine.dispose()


@pytest.mark.asyncio
async def test_postgres_remediation_integration():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        runbook_repo = PostgresRemediationRunbookRepository(session)
        attempt_repo = PostgresRemediationAttemptRepository(session)
        finding_repo = PostgresSystemFindingRepository(session)
        
        # Create Finding
        finding = await finding_repo.create_finding({
            "tenant_id": "t1",
            "source_type": "worker",
            "source_id": "w1",
            "source_hash": "hash_rem",
            "title": "Stuck worker",
            "description": "Worker is stuck",
            "severity": "MEDIUM",
            "risk_score": 35.0,
            "status": "OPEN"
        })
        
        # Create Runbook
        rb_data = {
            "name": "Restart Worker Service Integration",
            "action_type": "restart_worker",
            "severity_allowed": "MEDIUM",
            "requires_human_gate": False,
            "enabled": True,
            "execution_mode": "AUTO_SAFE",
            "max_attempts": 2,
            "cooldown_seconds": 60
        }
        rb = await runbook_repo.create_runbook(rb_data)
        assert rb["id"].startswith("rbk_")
        assert rb["name"] == rb_data["name"]
        
        # List Runbooks
        rbs = await runbook_repo.list_runbooks()
        assert len(rbs) == 1
        
        # Get Runbook
        fetched_rb = await runbook_repo.get_runbook(rb["id"])
        assert fetched_rb is not None
        assert fetched_rb["name"] == rb_data["name"]
        
        # Get Runbook by name
        fetched_rb_by_name = await runbook_repo.get_runbook_by_name(rb_data["name"])
        assert fetched_rb_by_name is not None
        assert fetched_rb_by_name["id"] == rb["id"]
        
        # Update Runbook Enabled
        updated_rb = await runbook_repo.update_runbook_enabled(rb["id"], False)
        assert updated_rb["enabled"] is False
        
        # Create Attempt
        att_data = {
            "finding_id": finding["id"],
            "runbook_id": rb["id"],
            "action_type": "restart_worker",
            "status": "RUNNING",
            "attempt_no": 1,
            "before_health": {"status": "HEALTHY"}
        }
        att = await attempt_repo.create_attempt(att_data)
        assert att["id"].startswith("att_")
        assert att["status"] == "RUNNING"
        
        # Get Attempt
        fetched_att = await attempt_repo.get_attempt(att["id"])
        assert fetched_att is not None
        assert fetched_att["status"] == "RUNNING"
        
        # Get Latest Attempt for finding
        latest_att = await attempt_repo.get_latest_attempt_for_finding(finding["id"])
        assert latest_att is not None
        assert latest_att["id"] == att["id"]
        
        # List attempts by finding
        atts_by_finding = await attempt_repo.list_attempts_by_finding(finding["id"])
        assert len(atts_by_finding) == 1
        
        # List attempts
        atts = await attempt_repo.list_attempts()
        assert len(atts) == 1
        
        # Update Attempt
        updated_att = await attempt_repo.update_attempt(att["id"], {"status": "SUCCEEDED", "error_message": "None"})
        assert updated_att["status"] == "SUCCEEDED"
        
    await engine.dispose()



