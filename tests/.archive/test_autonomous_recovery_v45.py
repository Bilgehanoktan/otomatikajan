import asyncio
import pytest
from packages.orchestration.application.job_queue import JobQueue, JobStatus
from packages.orchestration.agi.cognitive.metacognitive_auditor import metacognitive_auditor
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_autonomous_job_recovery_logic():
    """
    Test the self-healing cycle:
    Failure -> Audit -> Re-queue with Context
    """
    # 1. Setup local queue
    queue = JobQueue(concurrency=1)
    
    # 2. Mock handler that fails on first attempt but succeeds if recovery_context exists
    async def mock_handler(**payload):
        if not payload.get("recovery_context"):
            raise ValueError("Missing critical recovery context!")
        return "Recovered Successfully!"

    queue.register("test_recovery_job", mock_handler)
    
    # 3. Mock MetacognitiveAuditor to suggest recovery
    with patch("packages.orchestration.application.job_queue.metacognitive_auditor.analyze_job_failure", new_callable=AsyncMock) as mock_audit:
        mock_audit.return_value = {
            "recoverable": True,
            "root_cause": "Context missing in initial payload",
            "inhibition_injection": "Don't ignore the hidden context",
            "context_augmentation": "Here is the missing piece of information"
        }
        
        # 4. Enqueue and start worker
        job = await queue.enqueue("test_recovery_job", input="raw_data")
        
        # Manually run one cycle of worker logic or start/stop
        worker_task = asyncio.create_task(queue.start(num_workers=1))
        
        # Wait for the job to fail once, be audited, and requeued
        # We need to wait enough for: 
        # 1. First run (fails)
        # 2. Audit (mocked)
        # 3. Re-queue
        # 4. Second run (succeeds with recovery_context)
        
        timeout = 15.0
        start = asyncio.get_event_loop().time()
        while job.status != JobStatus.COMPLETED and (asyncio.get_event_loop().time() - start) < timeout:
            await asyncio.sleep(0.5)
        
        await queue.stop()
        
        # 5. Assertions
        assert job.status == JobStatus.COMPLETED
        assert job.recovery_attempts == 1
        assert "recovery_context" in job.payload
        assert job.payload["recovery_context"] == "Here is the missing piece of information"
        assert job.result == "Recovered Successfully!"
        print("\n✅ Autonomous Recovery Test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_autonomous_job_recovery_logic())
