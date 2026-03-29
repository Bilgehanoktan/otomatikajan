import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from core.job_queue import JobQueue, Job, JobStatus


@pytest.mark.asyncio
async def test_worker_should_mark_job_error_when_execute_crashes():
    """
    Worker seviyesinde beklenmeyen exception gelirse job ERROR olmalı.
    """
    queue = JobQueue()

    job = await queue.enqueue("dummy_job")

    async def _boom(_job):
        raise RuntimeError("worker crash")

    queue._execute = _boom  # noqa: SLF001
    queue._running = True

    worker = asyncio.create_task(queue._worker("test-worker"))  # noqa: SLF001
    await asyncio.sleep(0.1)

    queue._running = False
    worker.cancel()
    await asyncio.gather(worker, return_exceptions=True)

    assert job.status == JobStatus.ERROR
    assert "Beklenmeyen Worker Hatası" in job.error


@pytest.mark.asyncio
async def test_zombie_sweeper_should_cancel_only_stale_running_jobs(monkeypatch):
    """
    30 dakikayı aşan RUNNING işler cancel edilmeli, taze işler edilmemeli.
    """
    queue = JobQueue()
    now = datetime.now(timezone.utc)

    fresh = Job(
        id="fresh-job",
        type="dummy",
        payload={},
        status=JobStatus.RUNNING,
        started_at=(now - timedelta(minutes=5)).isoformat(),
    )
    stale = Job(
        id="stale-job",
        type="dummy",
        payload={},
        status=JobStatus.RUNNING,
        started_at=(now - timedelta(minutes=31)).isoformat(),
    )
    done = Job(
        id="done-job",
        type="dummy",
        payload={},
        status=JobStatus.COMPLETED,
        started_at=(now - timedelta(minutes=45)).isoformat(),
    )

    queue._jobs = {fresh.id: fresh, stale.id: stale, done.id: done}  # noqa: SLF001
    queue._running = True

    cancelled = []

    def _record_cancel(job_id: str):
        cancelled.append(job_id)
        return True

    async def _one_tick_sleep(_seconds):
        queue._running = False

    monkeypatch.setattr(queue, "request_cancel", _record_cancel)
    monkeypatch.setattr("core.job_queue.asyncio.sleep", _one_tick_sleep, raising=True)

    await queue._zombie_sweeper()  # noqa: SLF001

    assert cancelled == ["stale-job"]


def test_request_cancel_should_mark_pending_job_as_error():
    """
    Kuyruktayken iptal edilen iş doğrudan ERROR durumuna çekilmeli.
    """
    queue = JobQueue()
    job = Job(
        id="job-1",
        type="dummy",
        payload={},
        status=JobStatus.PENDING,
    )
    queue._jobs[job.id] = job  # noqa: SLF001

    ok = queue.request_cancel(job.id)

    assert ok is True
    assert job.status == JobStatus.ERROR
    assert "iptal" in job.error.lower()
    assert job.completed_at
