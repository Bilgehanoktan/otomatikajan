from __future__ import annotations
import os
import pytest

def test_celery_backend_capabilities_are_explicit(monkeypatch) -> None:
    monkeypatch.setenv("QUEUE_BACKEND", "celery")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    # Force re-import or bypass lazy singleton for testing
    import core.job_queue
    from core.job_queue import CeleryJobQueue

    queue = CeleryJobQueue()
    assert queue.backend_name == "celery"
    assert queue.capabilities.supports_cancel is False
    assert queue.capabilities.supports_pause is False
    assert queue.capabilities.supports_resume is False
    assert queue.capabilities.listing_scope == "process_local"

def test_inprocess_backend_capabilities_are_explicit(monkeypatch) -> None:
    monkeypatch.setenv("QUEUE_BACKEND", "inprocess")
    monkeypatch.delenv("REDIS_URL", raising=False)

    from core.job_queue import JobQueue

    queue = JobQueue()
    assert queue.backend_name == "inprocess"
    assert queue.capabilities.supports_cancel is True
    assert queue.capabilities.supports_pause is True
    assert queue.capabilities.supports_resume is True
    assert queue.capabilities.listing_scope == "global"
