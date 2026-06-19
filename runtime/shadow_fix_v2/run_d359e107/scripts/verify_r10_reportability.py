import asyncio
import uuid
import json
from datetime import datetime, timezone
from libs.db.models.core_models import OperationalIncident, SovereignEvidence, Project, Base
from services.govern.reporting_service import IncidentReportingService
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

async def verify_r10_reportability():
    print("--- R-10 Reportability Verification (SQLite In-Memory) ---")
    
    # 1. Setup In-Memory DB
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # 2. Mock Project
        proj_id = uuid.uuid4()
        project = Project(
            id=proj_id,
            title="R-10 Chaos Load Test",
            status="RUNNING"
        )
        db.add(project)
        await db.flush()
        
        # 3. Mock Incident
        inc_id = uuid.uuid4()
        incident = OperationalIncident(
            id=inc_id,
            incident_type="regional_saturation",
            severity="high",
            message="Cross-region failover triggered due to EU-WEST saturation during soak test.",
            project_id=proj_id,
            payload={
                "root_cause": "Unpredicted burst during chaos injection.",
                "prevention_plan": "Automatic throttle on non-critical workloads."
            },
            resolved_at=datetime.now(timezone.utc)
        )
        db.add(incident)
        await db.flush()
        
        # 4. Mock Evidence Chain
        ev_diag = SovereignEvidence(
            evidence_type="diagnosis",
            severity="warning",
            project_id=proj_id,
            incident_id=inc_id,
            payload={
                "action": "Detected high CPU in EU-WEST",
                "reasoning": "CPU > 90% for 5 consecutive windows."
            }
        )
        ev_failover = SovereignEvidence(
            evidence_type="failover",
            severity="critical",
            project_id=proj_id,
            incident_id=inc_id,
            payload={
                "action": "Traffic steered to US-EAST",
                "source_region": "EU-WEST",
                "target_region": "US-EAST",
                "reason": "EU-WEST CPU Exhaustion",
                "latency_ms": 320,
                "cost_delta": 0.08
            }
        )
        db.add_all([ev_diag, ev_failover])
        await db.commit()
        
        # 5. Generate Reports using the injected session
        print(f"\n[Postmortem Generation Test] for Incident {inc_id}")
        # Note: We pass UUID objects directly now
        postmortem = await IncidentReportingService.generate_postmortem(inc_id, db=db)
        print(postmortem)
        
        print(f"\n[Evidence Pack Test] for Project {proj_id}")
        pack = await IncidentReportingService.generate_failover_evidence_pack(proj_id, db=db)
        print(json.dumps(pack, indent=2))
        
        print("\n[Executive Summary Test]")
        summary = await IncidentReportingService.generate_executive_summary(db=db)
        print(json.dumps(summary, indent=2))
        
    print("\n--- R-10 Verification COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(verify_r10_reportability())
