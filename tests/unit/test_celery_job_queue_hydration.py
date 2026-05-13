import uuid
from types import SimpleNamespace

import pytest


class _FakeSession:
    def __init__(self):
        self.commits = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self):
        self.commits += 1


class _FakeSessionFactory:
    def __init__(self, session):
        self.session = session

    def __call__(self):
        return self.session


class _FakeCelery:
    def __init__(self):
        self.sent = []

    def send_task(self, *args, **kwargs):
        self.sent.append((args, kwargs))


@pytest.mark.asyncio
async def test_celery_hydration_redispatches_stale_active_projects(monkeypatch):
    from libs.db import session as db_session
    from libs.db.repositories import repository
    from services.orchestration.application.job_queue import CeleryJobQueue

    queued_id = uuid.uuid4()
    stale_running_id = uuid.uuid4()
    projects = [
        SimpleNamespace(
            id=queued_id,
            title="Queued workflow",
            description="",
            status="QUEUED",
            job_id="",
            started_at=None,
            workflow_template="default",
            quality_profile="standard",
            acceptance_criteria=[],
            execution_context={},
        ),
        SimpleNamespace(
            id=stale_running_id,
            title="Stale running workflow",
            description="",
            status="RUNNING",
            job_id=None,
            started_at=None,
            workflow_template="coding",
            quality_profile="high_precision",
            acceptance_criteria=[],
            execution_context={},
        ),
    ]
    fake_session = _FakeSession()

    async def _list_recent(_db, limit=100):
        return projects

    monkeypatch.setattr(db_session, "AsyncSessionLocal", _FakeSessionFactory(fake_session))
    monkeypatch.setattr(repository.ProjectRepository, "list_recent", _list_recent)

    queue = object.__new__(CeleryJobQueue)
    queue.backend_name = "celery"
    queue._available = True
    queue._celery = _FakeCelery()
    queue._jobs = {}

    hydrated = await queue.hydrate_from_db()

    assert hydrated == 2
    assert len(queue._celery.sent) == 2
    assert projects[0].job_id == str(queued_id)
    assert projects[1].status == "QUEUED"
    assert projects[1].job_id == str(stale_running_id)
    assert fake_session.commits == 1
    sent_payloads = [call[1]["kwargs"] for call in queue._celery.sent]
    assert {payload["project_id"] for payload in sent_payloads} == {str(queued_id), str(stale_running_id)}
