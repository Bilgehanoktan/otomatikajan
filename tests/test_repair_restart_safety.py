import pytest
import asyncio
from core.repair_orchestrator import RepairOrchestrator
from packages.repair_engine.schemas.repair_job import RepairJob, RepairJobStatus
from packages.repair_engine.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_repair_job_reconstruction():
    """Verify that a RepairJob can be reconstructed from its DB-ready state."""
    orch = RepairOrchestrator()
    
    # Create a job with some Faz 12 data
    job = RepairJob.create("inc_123")
    job.status = RepairJobStatus.TRIAGED
    job.vector_context_used = True
    job.debate_triggered = True
    job.debate_result_summary = "Consensus reached"
    job.risk_score = 75
    
    # Mock a Record (simulate what comes from DB)
    class MockRecord:
        def __init__(self, job):
            self.job_id = job.job_id
            self.incident_id = job.incident_id
            self.status = job.status.value
            self.ticket_id = job.ticket_id
            self.plan_id = job.plan_id
            self.validation_id = job.validation_id
            self.pr_url = job.pr_url
            self.branch_name = job.branch_name
            self.diff = job.diff
            self.error_detail = job.error_detail
            self.history = job.history
            self.created_at = job.created_at
            self.updated_at = job.updated_at
            # This is what we updated in RepairJobRepo.upsert
            self.meta = {
                "vector_context_used": job.vector_context_used,
                "debate_triggered": job.debate_triggered,
                "debate_result_summary": job.debate_result_summary,
                "risk_score": job.risk_score,
                "canary_id": job.canary_id,
            }

    record = MockRecord(job)
    
    # Reconstruct
    reconstructed = orch._map_record_to_job(record)
    
    assert reconstructed.job_id == job.job_id
    assert reconstructed.status == RepairJobStatus.TRIAGED
    assert reconstructed.vector_context_used is True
    assert reconstructed.debate_triggered is True
    assert reconstructed.debate_result_summary == "Consensus reached"
    assert reconstructed.risk_score == 75
