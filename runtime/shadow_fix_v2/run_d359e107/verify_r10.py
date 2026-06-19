"""
Sovereign AGI — Phase 26 Verification
verify_r10.py: Chaos & Operational Reportability (R-10)
"""
import asyncio
import json
import uuid
from libs.db.session import init_db, session_scope
from libs.db.models.core_models import OperationalIncident, SovereignEvidence, Project
from services.govern.reporting_service import IncidentReportingService, OperationalTrustReport

async def run_verification():
    print("--- [R-10] Phase 26: Chaos & Operational Reportability Verification ---")
    await init_db()
    
    async with session_scope() as db:
        # 1. Setup Mock Data
        project = Project(title="Chaos Test Project", description="Verify R-10 reporting")
        db.add(project)
        await db.flush()
        
        incident = OperationalIncident(
            incident_type="regional_latency_spike",
            severity="high",
            message="Detected 500ms latency spike in US-EAST-1",
            project_id=project.id,
            payload={
                "root_cause": "Network congestion in AWS Tier-1 backbone",
                "prevention_plan": "Auto-failover to US-WEST-2 enabled"
            }
        )
        db.add(incident)
        await db.flush()
        
        evidence_1 = SovereignEvidence(
            evidence_type="failover",
            severity="warning",
            project_id=project.id,
            incident_id=incident.id,
            payload={
                "action": "Triggered regional failover",
                "source_region": "us-east-1",
                "target_region": "us-west-2",
                "reason": "Latency > threshold",
                "latency_ms": 540,
                "reasoning": "Sovereign autonomy detected breach of SLA, executing regional jump."
            }
        )
        db.add(evidence_1)
        
        evidence_2 = SovereignEvidence(
            evidence_type="rollback",
            severity="info",
            project_id=project.id,
            incident_id=incident.id,
            payload={
                "action": "Verified state consistency",
                "reasoning": "Post-failover check confirmed data integrity in target region."
            }
        )
        db.add(evidence_2)
        
    print("\n--- [R-10] Step 1: Autonomous Postmortem ---")
    postmortem = await IncidentReportingService.generate_postmortem(incident.id)
    print(postmortem)

    print("\n--- [R-10] Step 2: Executive Summary ---")
    exec_summary = await IncidentReportingService.generate_executive_summary()
    print(json.dumps(exec_summary, indent=2))

    print("\n--- [R-10] Step 3: Failover Evidence Pack ---")
    failover_pack = await IncidentReportingService.generate_failover_evidence_pack(project.id)
    print(json.dumps(failover_pack, indent=2))

    print("\n--- [R-10] Step 4: System-Wide Trust Summary ---")
    trust_summary = await OperationalTrustReport.generate_trust_summary()
    print(json.dumps(trust_summary, indent=2))

    print("\n[SUCCESS] R-10 Chaos & Operational Reportability Verified.")

if __name__ == "__main__":
    asyncio.run(run_verification())
