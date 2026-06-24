import os
import pytest
import asyncio
import unittest.mock
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy import select, update

from apps.bilgeapi.memory.db import init_workspace_db, get_workspace_db_session, get_workspace_engine, _engines
from apps.bilgeapi.memory.models import TaskModel, AuditLogModel, DecisionModel
from apps.bilgeapi.memory.repositories import (
    SystemRepository, TaskRepository, AuditLogRepository, DecisionRepository
)
from apps.bilgeapi.orchestration.retry_policy import RetryPolicy
from apps.bilgeapi.orchestration.task_queue import TaskQueue
from apps.bilgeapi.orchestration.worker import TaskWorker
from apps.bilgeapi.core.workspace import WorkspaceManager

@pytest.fixture
async def mock_workspace(monkeypatch):
    """
    Async fixture that overrides WorkspaceManager to use a temporary directory
    for the database, initializes the schema, and disposes of all engines on cleanup.
    """
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()
        
        def mock_init(self, *args, **kwargs):
            self.start_path = tmp_path
            self.project_root = tmp_path
            self.workspace_dir = tmp_path
            
        monkeypatch.setattr(WorkspaceManager, "__init__", mock_init)
        
        await init_workspace_db(tmp_path)
        
        yield tmp_path
        
        # Clean up database engines to prevent file locking on Windows
        from apps.bilgeapi.memory.db import _engines
        for eng in list(_engines.values()):
            await eng.dispose()
        _engines.clear()

@pytest.mark.asyncio
async def test_task_enqueue_dequeue(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    # Instantiate queue
    queue = TaskQueue()

    # Enqueue task
    async with get_workspace_db_session(tmp_path) as session:
        task = await queue.enqueue(
            system_id=system_id,
            title="Test Enqueue Task",
            agent_role="specialist",
            action_type="TEST_ACTION",
            risk_level="LOW",
            payload={"param": 1},
            session=session
        )
        assert task["status"] == "PENDING"
        assert task["attempt_count"] == 0

    # Verify TASK_CREATED audit log
    async with get_workspace_db_session(tmp_path) as session:
        stmt = select(AuditLogModel).where(AuditLogModel.event_type == "TASK_CREATED")
        res = await session.execute(stmt)
        audit = res.scalar_one_or_none()
        assert audit is not None
        assert audit.status == "ALLOWED"

    # Dequeue task
    async with get_workspace_db_session(tmp_path) as session:
        dq_task = await queue.dequeue(session)
        assert dq_task is not None
        assert dq_task["id"] == task["id"]
        assert dq_task["status"] == "RUNNING"
        assert dq_task["attempt_count"] == 1

    # Verify TASK_DEQUEUED audit log
    async with get_workspace_db_session(tmp_path) as session:
        stmt = select(AuditLogModel).where(AuditLogModel.event_type == "TASK_DEQUEUED")
        res = await session.execute(stmt)
        audit = res.scalar_one_or_none()
        assert audit is not None
        assert audit.status == "ALLOWED"

    # Complete task
    async with get_workspace_db_session(tmp_path) as session:
        comp_task = await queue.complete_task(task["id"], session)
        assert comp_task["status"] == "COMPLETED"

    # Verify TASK_COMPLETED audit log
    async with get_workspace_db_session(tmp_path) as session:
        stmt = select(AuditLogModel).where(AuditLogModel.event_type == "TASK_COMPLETED")
        res = await session.execute(stmt)
        audit = res.scalar_one_or_none()
        assert audit is not None

@pytest.mark.asyncio
async def test_task_retry_and_limit(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    # Retry policy with max attempts = 2
    policy = RetryPolicy()
    policy.base_delay = 1.0
    policy.factor = 2.0
    
    queue = TaskQueue(retry_policy=policy)

    # Enqueue
    async with get_workspace_db_session(tmp_path) as session:
        task = await queue.enqueue(
            system_id=system_id,
            title="Retry limit test",
            agent_role="specialist",
            action_type="TEST_ACTION",
            risk_level="LOW",
            payload={"max_attempts": 2},
            session=session
        )
        
        # Manually force max_attempts = 2 in DB
        db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task["id"]))).scalar_one()
        db_task.max_attempts = 2
        await session.flush()

    # Dequeue 1
    async with get_workspace_db_session(tmp_path) as session:
        dq1 = await queue.dequeue(session)
        assert dq1["attempt_count"] == 1

    # Fail 1 -> Should reschedule retry
    async with get_workspace_db_session(tmp_path) as session:
        f1 = await queue.fail_task(task["id"], "Transient error 1", session)
        assert f1["status"] == "PENDING"
        assert f1["attempt_count"] == 1

    # Verify TASK_RETRY_SCHEDULED audit log
    async with get_workspace_db_session(tmp_path) as session:
        stmt = select(AuditLogModel).where(AuditLogModel.event_type == "TASK_RETRY_SCHEDULED")
        res = await session.execute(stmt)
        assert res.scalar_one_or_none() is not None

    # Dequeue immediately -> Should return None (due to backoff time)
    async with get_workspace_db_session(tmp_path) as session:
        dq2_immediate = await queue.dequeue(session)
        assert dq2_immediate is None

    # Fast forward time in DB
    async with get_workspace_db_session(tmp_path) as session:
        upd_stmt = update(TaskModel).where(TaskModel.id == task["id"]).values(
            updated_at=datetime.now(timezone.utc) - timedelta(seconds=10)
        )
        await session.execute(upd_stmt)
        await session.commit()

    # Dequeue 2
    async with get_workspace_db_session(tmp_path) as session:
        dq2 = await queue.dequeue(session)
        assert dq2 is not None
        assert dq2["attempt_count"] == 2

    # Fail 2 -> Max attempts (2) reached, should fail permanently
    async with get_workspace_db_session(tmp_path) as session:
        f2 = await queue.fail_task(task["id"], "Transient error 2", session)
        assert f2["status"] == "FAILED"

    # Verify TASK_PERMANENTLY_FAILED audit log
    async with get_workspace_db_session(tmp_path) as session:
        stmt = select(AuditLogModel).where(AuditLogModel.event_type == "TASK_PERMANENTLY_FAILED")
        res = await session.execute(stmt)
        assert res.scalar_one_or_none() is not None

@pytest.mark.asyncio
async def test_stale_running_task_recovery(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    queue = TaskQueue()

    # Enqueue and dequeue to make it RUNNING
    async with get_workspace_db_session(tmp_path) as session:
        task = await queue.enqueue(system_id, "Stale task", "specialist", "TEST", "LOW", {}, session)
        await queue.dequeue(session)

    # Force updated_at back in time to simulate stale task
    async with get_workspace_db_session(tmp_path) as session:
        upd_stmt = update(TaskModel).where(TaskModel.id == task["id"]).values(
            updated_at=datetime.now(timezone.utc) - timedelta(seconds=60)
        )
        await session.execute(upd_stmt)
        await session.commit()

    # Run recovery (timeout 30s)
    async with get_workspace_db_session(tmp_path) as session:
        recovered_count = await queue.recover_stale_tasks(30.0, session)
        assert recovered_count == 1

    # Task should have failed and moved back to PENDING (since attempt_count=1 < max_attempts=3)
    async with get_workspace_db_session(tmp_path) as session:
        db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task["id"]))).scalar_one()
        assert db_task.status == "PENDING"

@pytest.mark.asyncio
async def test_worker_execution_flow(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    worker = TaskWorker(workspace_dir=tmp_path)
    
    async def mock_handler(task_dict):
        return f"Result containing secret: api_key = 'super_secret_value'"

    worker.register_executor("RUN_MOCK", mock_handler)

    async with get_workspace_db_session(tmp_path) as session:
        task = await worker.task_queue.enqueue(
            system_id=system_id,
            title="Run mock action",
            agent_role="specialist",
            action_type="RUN_MOCK",
            risk_level="LOW",
            payload={},
            session=session
        )

    # Start worker loop
    await worker.start()
    await asyncio.sleep(0.5)
    await worker.stop()

    # Task should be COMPLETED
    async with get_workspace_db_session(tmp_path) as session:
        db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task["id"]))).scalar_one()
        assert db_task.status == "COMPLETED"

@pytest.mark.asyncio
async def test_worker_unknown_action_denied(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    worker = TaskWorker(workspace_dir=tmp_path)

    async with get_workspace_db_session(tmp_path) as session:
        task = await worker.task_queue.enqueue(
            system_id=system_id,
            title="Unknown action test",
            agent_role="specialist",
            action_type="UNREGISTERED_ACTION",
            risk_level="LOW",
            payload={},
            session=session
        )

    await worker.start()
    await asyncio.sleep(0.5)
    await worker.stop()

    # Task should be FAILED
    async with get_workspace_db_session(tmp_path) as session:
        db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task["id"]))).scalar_one()
        assert db_task.status == "FAILED"

        # Check audit log for UNREGISTERED_ACTION_DENIED
        stmt = select(AuditLogModel).where(AuditLogModel.event_type == "UNREGISTERED_ACTION_DENIED")
        audit = (await session.execute(stmt)).scalar_one_or_none()
        assert audit is not None
        assert audit.status == "DENIED"

@pytest.mark.asyncio
async def test_worker_concurrency_limit(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    worker = TaskWorker(workspace_dir=tmp_path, concurrency=1)

    async def slow_handler(t):
        await asyncio.sleep(0.5)
        return "done"

    worker.register_executor("SLOW_ACTION", slow_handler)

    async with get_workspace_db_session(tmp_path) as session:
        t1 = await worker.task_queue.enqueue(system_id, "Task 1", "specialist", "SLOW_ACTION", "LOW", {}, session)
        t2 = await worker.task_queue.enqueue(system_id, "Task 2", "specialist", "SLOW_ACTION", "LOW", {}, session)

    await worker.start()
    await asyncio.sleep(0.1)

    # Exactly 1 task should be RUNNING, the other PENDING
    async with get_workspace_db_session(tmp_path) as session:
        db_t1 = (await session.execute(select(TaskModel).where(TaskModel.id == t1["id"]))).scalar_one()
        db_t2 = (await session.execute(select(TaskModel).where(TaskModel.id == t2["id"]))).scalar_one()
        
        statuses = {db_t1.status, db_t2.status}
        assert statuses == {"RUNNING", "PENDING"}

    # Wait for both to finish
    await asyncio.sleep(0.7)
    await worker.stop()

    async with get_workspace_db_session(tmp_path) as session:
        db_t1 = (await session.execute(select(TaskModel).where(TaskModel.id == t1["id"]))).scalar_one()
        db_t2 = (await session.execute(select(TaskModel).where(TaskModel.id == t2["id"]))).scalar_one()
        assert db_t1.status == "COMPLETED"
        assert db_t2.status == "COMPLETED"

@pytest.mark.asyncio
async def test_worker_graceful_shutdown(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    worker = TaskWorker(workspace_dir=tmp_path)
    
    async def slow_handler(t):
        await asyncio.sleep(0.3)
        return "done"

    worker.register_executor("SLOW", slow_handler)

    async with get_workspace_db_session(tmp_path) as session:
        t = await worker.task_queue.enqueue(system_id, "Shutdown task", "specialist", "SLOW", "LOW", {}, session)

    await worker.start()
    await asyncio.sleep(0.1)
    
    await worker.stop(timeout=1.0)

    async with get_workspace_db_session(tmp_path) as session:
        db_t = (await session.execute(select(TaskModel).where(TaskModel.id == t["id"]))).scalar_one()
        assert db_t.status == "COMPLETED"

@pytest.mark.asyncio
async def test_worker_graceful_shutdown_timeout(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    worker = TaskWorker(workspace_dir=tmp_path)
    
    async def very_slow_handler(t):
        await asyncio.sleep(2.0)
        return "done"

    worker.register_executor("VERY_SLOW", very_slow_handler)

    async with get_workspace_db_session(tmp_path) as session:
        t = await worker.task_queue.enqueue(system_id, "Timeout task", "specialist", "VERY_SLOW", "LOW", {}, session)

    await worker.start()
    await asyncio.sleep(0.1)
    
    await worker.stop(timeout=0.2)

    # Task should be transitioned back to PENDING since it was cancelled
    async with get_workspace_db_session(tmp_path) as session:
        db_t = (await session.execute(select(TaskModel).where(TaskModel.id == t["id"]))).scalar_one()
        assert db_t.status == "PENDING"

@pytest.mark.asyncio
async def test_pending_approved_execution(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    worker = TaskWorker(workspace_dir=tmp_path)
    
    async def mock_handler(t):
        return "ok"

    worker.register_executor("RUN", mock_handler)

    async with get_workspace_db_session(tmp_path) as session:
        task = await worker.task_queue.enqueue(system_id, "Approved task", "specialist", "RUN", "HIGH", {}, session)
        
        # Manually update status to PENDING_APPROVED
        db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task["id"]))).scalar_one()
        db_task.status = "PENDING_APPROVED"
        await session.flush()

    await worker.start()
    await asyncio.sleep(0.5)
    await worker.stop()

    # Task should be executed and COMPLETED
    async with get_workspace_db_session(tmp_path) as session:
        db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task["id"]))).scalar_one()
        assert db_task.status == "COMPLETED"

@pytest.mark.asyncio
async def test_blocked_not_executed(mock_workspace):
    tmp_path = mock_workspace
    
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="Orchestration Test",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]

    worker = TaskWorker(workspace_dir=tmp_path)
    
    async def mock_handler(t):
        return "ok"

    worker.register_executor("RUN", mock_handler)

    async with get_workspace_db_session(tmp_path) as session:
        task = await worker.task_queue.enqueue(system_id, "Blocked task", "specialist", "RUN", "HIGH", {}, session)
        
        # Manually update status to BLOCKED
        db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task["id"]))).scalar_one()
        db_task.status = "BLOCKED"
        await session.flush()

    await worker.start()
    await asyncio.sleep(0.5)
    await worker.stop()

    # Task should remain BLOCKED
    async with get_workspace_db_session(tmp_path) as session:
        db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task["id"]))).scalar_one()
        assert db_task.status == "BLOCKED"
