import asyncio

import pytest

from workers.workflow_worker.tasks import project_tasks


class _FakeAsyncEngine:
    def __init__(self):
        self.dispose_calls = 0

    async def dispose(self):
        self.dispose_calls += 1


def _install_fake_engine(monkeypatch):
    import libs.db.session as db_session

    engine = _FakeAsyncEngine()
    monkeypatch.setattr(db_session, "_engine", engine)
    monkeypatch.setattr(db_session, "_async_session_factory", object())
    monkeypatch.setattr(db_session, "_last_loop", object())
    return db_session, engine


def test_terminal_project_errors_are_acknowledged_without_retry():
    assert project_tasks._is_terminal_project_result(
        {"status": "error", "reason": "not_found"}
    )
    assert project_tasks._is_terminal_project_result(
        {"status": "error", "reason": "missing_project_id"}
    )
    assert not project_tasks._is_terminal_project_result(
        {"status": "error", "reason": "database_unavailable"}
    )


def test_run_async_disposes_engine_before_closing_loop(monkeypatch):
    db_session, engine = _install_fake_engine(monkeypatch)

    assert project_tasks.run_async(asyncio.sleep(0, result="ok")) == "ok"

    assert engine.dispose_calls == 1
    assert db_session._engine is None
    assert db_session._async_session_factory is None
    assert db_session._last_loop is None


@pytest.mark.asyncio
async def test_run_async_disposes_engine_in_worker_thread(monkeypatch):
    db_session, engine = _install_fake_engine(monkeypatch)

    result = project_tasks.run_async(asyncio.sleep(0, result="thread-ok"))

    assert result == "thread-ok"
    assert engine.dispose_calls == 1
    assert db_session._engine is None
    assert db_session._async_session_factory is None
    assert db_session._last_loop is None


def test_run_project_task_returns_terminal_not_found_without_side_effects(monkeypatch):
    def fake_run_async(coro):
        coro.close()
        return {"status": "error", "reason": "not_found"}

    def unexpected_webhook(*args, **kwargs):
        raise AssertionError("terminal missing projects must not emit failure webhooks")

    monkeypatch.setattr(project_tasks, "run_async", fake_run_async)
    monkeypatch.setattr(project_tasks.send_webhook_task, "apply_async", unexpected_webhook)

    result = project_tasks.run_project_task.run(
        db_project_id="11111111-1111-1111-1111-111111111111",
        title="stale restored task",
        job_id="stale-job",
    )

    assert result == {"status": "error", "reason": "not_found", "terminal": True}
