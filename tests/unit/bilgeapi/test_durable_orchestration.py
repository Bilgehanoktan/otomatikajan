import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from apps.bilgeapi.models.database import Base, AgentTaskQueueModel, AgentTaskLeaseModel, AgentOrchestrationRunModel
from apps.bilgeapi.orchestration.durable_queue import DurableAgentQueue
from apps.bilgeapi.services.ceo_orchestrator import CEOOrcAgent


@pytest.fixture
async def db_session():
    """Sets up an isolated in-memory SQLite database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with engine.begin() as conn:
        try:
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    AgentTaskQueueModel.__table__,
                    AgentTaskLeaseModel.__table__,
                    AgentOrchestrationRunModel.__table__,
                ],
                checkfirst=True
            ))
        except Exception:
            pass
        
    async with async_session() as session:
        yield session
        
    await engine.dispose()


@pytest.mark.asyncio
async def test_durable_queue_lifecycle(db_session):
    queue = DurableAgentQueue(default_max_attempts=3)
    
    # 1. Enqueue task
    task = await queue.enqueue_task(
        session=db_session,
        agent_role="TEST_AGENT",
        action_type="RUN_TEST",
        payload={"foo": "bar"},
        risk_level="low",
        priority_score=5.0,
        idempotency_key="unique_key_123"
    )
    assert task.task_id.startswith("task_")
    assert task.status == "PENDING"
    assert task.payload == {"foo": "bar"}
    
    # Verify idempotency
    dup_task = await queue.enqueue_task(
        session=db_session,
        agent_role="TEST_AGENT",
        action_type="RUN_TEST",
        idempotency_key="unique_key_123"
    )
    assert dup_task.task_id == task.task_id
    
    # 2. Acquire task (Lease it)
    leased = await queue.acquire_next_task(db_session, lease_owner="worker_alice")
    assert leased is not None
    assert leased.task_id == task.task_id
    assert leased.status == "RUNNING"
    assert leased.attempt_count == 1
    
    # Verify lease exists in DB
    stmt = select(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == task.task_id)
    res = await db_session.execute(stmt)
    lease = res.scalar_one_or_none()
    assert lease is not None
    assert lease.lease_owner == "worker_alice"
    
    # 3. Try to acquire again when already leased (should return None)
    no_task = await queue.acquire_next_task(db_session, lease_owner="worker_bob")
    assert no_task is None
    
    # 4. Complete task
    await queue.complete_task(db_session, task.task_id, execution_summary="success", ledger_hash="hash_val")
    
    # Verify lease is removed
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is None
    
    # Verify run summary recorded
    run_stmt = select(AgentOrchestrationRunModel).where(AgentOrchestrationRunModel.task_id == task.task_id)
    run_res = await db_session.execute(run_stmt)
    run = run_res.scalar_one_or_none()
    assert run is not None
    assert run.status == "COMPLETED"
    assert run.execution_summary == "success"
    assert run.evidence_ledger_hash == "hash_val"


@pytest.mark.asyncio
async def test_durable_queue_stale_lease_recovery(db_session):
    queue = DurableAgentQueue(default_max_attempts=2)
    
    # Enqueue and lease
    task = await queue.enqueue_task(
        session=db_session,
        agent_role="TEST_AGENT",
        action_type="RUN_TEST",
        max_attempts=2
    )
    leased = await queue.acquire_next_task(db_session, lease_owner="worker_alice", lease_duration_seconds=120)
    assert leased is not None
    
    # Manually backdate lease expiration to simulate timeout/stale lease
    stmt = select(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == task.task_id)
    res = await db_session.execute(stmt)
    lease = res.scalar_one()
    lease.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    await db_session.flush()
    
    # Run recovery
    recovered = await queue.recover_stale_leases(db_session)
    assert recovered == 1
    
    # Verify task went back to PENDING (since attempt_count 1 < max_attempts 2)
    assert task.status == "PENDING"
    
    # Acquire again -> attempt_count becomes 2
    leased2 = await queue.acquire_next_task(db_session, lease_owner="worker_bob")
    assert leased2 is not None
    assert leased2.attempt_count == 2
    
    # Expire lease again
    res = await db_session.execute(stmt)
    lease2 = res.scalar_one()
    lease2.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    await db_session.flush()
    
    # Run recovery again -> should fail task because attempt_count == max_attempts
    recovered2 = await queue.recover_stale_leases(db_session)
    assert recovered2 == 1
    assert task.status == "FAILED"


@pytest.mark.asyncio
async def test_ceo_orchestrator_flow(db_session):
    queue = DurableAgentQueue(default_max_attempts=3)
    ceo = CEOOrcAgent(queue)
    
    # 1. Initialize resolution
    ceo_task_id = await ceo.initialize_resolution(db_session, incident_id="inc_456")
    assert ceo_task_id is not None
    
    # CEO task starts as PENDING, let's lease it
    ceo_task = await queue.acquire_next_task(db_session, lease_owner="ceo_worker")
    assert ceo_task.status == "RUNNING"
    
    # 2. Step 1: INIT -> ANALYSIS
    res1 = await ceo.orchestrate_next_step(db_session, ceo_task_id)
    assert res1["status"] == "RUNNING"
    assert res1["phase"] == "ANALYSIS"
    
    analyst_task_id = ceo_task.payload["analyst_task_id"]
    assert analyst_task_id is not None
    
    # Simulate Analyst task RUNNING -> COMPLETED
    analyst_task = await queue.acquire_next_task(db_session, lease_owner="analyst_worker")
    await queue.complete_task(db_session, analyst_task_id, execution_summary="Analyst log")
    
    # 3. Step 2: ANALYSIS -> VERIFICATION
    res2 = await ceo.orchestrate_next_step(db_session, ceo_task_id)
    assert res2["status"] == "RUNNING"
    assert res2["phase"] == "VERIFICATION"
    
    tester_id = ceo_task.payload["tester_task_id"]
    security_id = ceo_task.payload["security_task_id"]
    assert tester_id is not None
    assert security_id is not None
    
    # Simulate Tester and Security task execution
    t_task = await queue.acquire_next_task(db_session, lease_owner="tester_worker")
    s_task = await queue.acquire_next_task(db_session, lease_owner="security_worker")
    await queue.complete_task(db_session, tester_id, execution_summary="Reproduced")
    await queue.complete_task(db_session, security_id, execution_summary="Secure")
    
    # 4. Step 3: VERIFICATION -> REPAIR
    res3 = await ceo.orchestrate_next_step(db_session, ceo_task_id)
    assert res3["status"] == "RUNNING"
    assert res3["phase"] == "REPAIR"
    
    repair_id = ceo_task.payload["repair_task_id"]
    assert repair_id is not None
    
    # Simulate Repair execution
    r_task = await queue.acquire_next_task(db_session, lease_owner="repair_worker")
    await queue.complete_task(db_session, repair_id, execution_summary="Patched")
    
    # 5. Step 4: REPAIR -> REVIEW
    res4 = await ceo.orchestrate_next_step(db_session, ceo_task_id)
    assert res4["status"] == "RUNNING"
    assert res4["phase"] == "REVIEW"
    
    reviewer_id = ceo_task.payload["reviewer_task_id"]
    assert reviewer_id is not None
    
    # Simulate Review execution
    rev_task = await queue.acquire_next_task(db_session, lease_owner="reviewer_worker")
    await queue.complete_task(db_session, reviewer_id, execution_summary="Approved")
    
    # 6. Step 5: REVIEW -> DONE
    res5 = await ceo.orchestrate_next_step(db_session, ceo_task_id)
    assert res5["status"] == "COMPLETED"
    assert res5["phase"] == "DONE"
    
    # CEO task should be completed now
    assert ceo_task.status == "COMPLETED"
