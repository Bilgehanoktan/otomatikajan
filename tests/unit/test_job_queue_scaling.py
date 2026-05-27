import pytest
from services.orchestration.application.job_queue import JobQueue

@pytest.mark.asyncio
async def test_job_queue_scaling():
    """
    Verifies that the asyncio JobQueue can dynamically scale its workers and semaphore concurrency level at runtime.
    """
    # Create an isolated in-process JobQueue instance for testing
    queue = JobQueue(concurrency=2)
    assert queue._concurrency == 2
    
    # Scale to 4 workers
    await queue.scale(4)
    assert queue._concurrency == 4
    
    # Clean up workers
    await queue.stop()
