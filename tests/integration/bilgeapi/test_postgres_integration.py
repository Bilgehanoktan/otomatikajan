import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from libs.db.base import Base
from apps.bilgeapi.models.database import (
    IncidentModel, DiagnosticRunModel, FindingModel, RecommendationModel,
    RepairRequestModel, AuditEventModel, WebhookDeliveryModel
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
    PostgresWebhookDeliveryRepository
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

