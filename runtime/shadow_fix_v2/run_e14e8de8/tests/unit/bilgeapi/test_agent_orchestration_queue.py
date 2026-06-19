import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from libs.db.base import Base
from apps.bilgeapi.models.database import (
    AgentTaskQueueModel,
    AgentTaskLeaseModel,
    AgentOrchestrationRunModel
)
from services.orchestration.application.agent_queue import AgentOrchestrationQueue

@pytest.fixture
async def mock_db():
    """
    In-memory SQLite async engine fixture.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # Create all tables on Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    @asynccontextmanager
    async def mock_session_scope():
        async with async_session() as session:
            yield session
            
    with patch("services.orchestration.application.agent_queue.session_scope", mock_session_scope):
        yield async_session

@pytest.fixture(autouse=True)
def mock_kinetic_arbiter():
    with patch("services.orchestration.application.agent_queue.kinetic_arbiter") as mock_arbiter:
        mock_arbiter.acquire_slot = AsyncMock(return_value=True)
        mock_arbiter.release_slot = MagicMock()
        yield mock_arbiter

@pytest.mark.asyncio
async def test_enqueue_priority_and_idempotency(mock_db):
    queue = AgentOrchestrationQueue()
    
    # Enqueue a task
    t1 = await queue.enqueue(
        task_id="t1",
        source="system",
        agent_role="architect",
        action_type="clear_local_cache",
        risk_level="low",
        idempotency_key="key_1"
    )
    
    assert t1["task_id"] == "t1"
    assert t1["status"] == "PENDING"
    assert t1["idempotency_key"] == "key_1"
    assert t1["priority_score"] > 0
    
    # Try enqueuing a duplicate idempotency key
    t1_dup = await queue.enqueue(
        task_id="t1_dup",
        source="system",
        agent_role="architect",
        action_type="clear_local_cache",
        risk_level="low",
        idempotency_key="key_1"
    )
    
    # Must return the existing task
    assert t1_dup["task_id"] == "t1"

@pytest.mark.asyncio
async def test_low_risk_auto_run_flow(mock_db):
    queue = AgentOrchestrationQueue()
    
    # Enqueue a low-risk, safe action
    await queue.enqueue(
        task_id="t_low",
        source="system",
        agent_role="planner",
        action_type="clear_local_cache",
        risk_level="low"
    )
    
    # Mock settings.BILGEAPI_AUTONOMY_MODE to SAFE_AUTONOMY
    with patch("apps.bilgeapi.services.autonomy_decision.settings") as mock_settings:
        from apps.bilgeapi.services.autonomy_decision import AutonomyMode
        mock_settings.BILGEAPI_AUTONOMY_MODE = AutonomyMode.SAFE_AUTONOMY
        
        # Process the task
        processed = await queue.process_next(context="test_worker")
        
        assert processed is not None
        assert processed["task_id"] == "t_low"
        assert processed["status"] == "COMPLETED"
        
        # Check run model persisted in DB
        async with mock_db() as db:
            res = await db.execute(select(AgentOrchestrationRunModel).where(AgentOrchestrationRunModel.task_id == "t_low"))
            run = res.scalar_one_or_none()
            assert run is not None
            assert run.status == "COMPLETED"

@pytest.mark.asyncio
async def test_high_risk_requires_human_gate(mock_db):
    queue = AgentOrchestrationQueue()
    
    # Enqueue a high-risk action (sandbox_retry has risk score modifier +10.0,
    # severity high is +50.0. Total is 60.0 which falls into HIGH risk level.
    # If we use db_migration (+30.0), total is 80.0 which maps to CRITICAL and gets BLOCKED).
    await queue.enqueue(
        task_id="t_high",
        source="system",
        agent_role="devops",
        action_type="sandbox_retry",
        risk_level="high"
    )
    
    with patch("apps.bilgeapi.services.autonomy_decision.settings") as mock_settings, \
         patch("services.orchestration.application.agent_queue.consensus_arbiter") as mock_arbiter:
        from apps.bilgeapi.services.autonomy_decision import AutonomyMode
        mock_settings.BILGEAPI_AUTONOMY_MODE = AutonomyMode.SAFE_AUTONOMY
        mock_arbiter.execute_debate = AsyncMock(return_value=(True, {}))
        
        processed = await queue.process_next(context="test_worker")
        
        assert processed is not None
        assert processed["task_id"] == "t_high"
        # Since risk level is HIGH, even if consensus approves, it must route to HUMAN_GATE_REQUIRED
        assert processed["status"] == "HUMAN_GATE_REQUIRED"

@pytest.mark.asyncio
async def test_critical_risk_blocked(mock_db):
    queue = AgentOrchestrationQueue()
    
    await queue.enqueue(
        task_id="t_crit",
        source="system",
        agent_role="devops",
        action_type="git_merge",
        risk_level="critical"
    )
    
    with patch("apps.bilgeapi.services.autonomy_decision.settings") as mock_settings, \
         patch("services.orchestration.application.agent_queue.consensus_arbiter") as mock_arbiter:
        from apps.bilgeapi.services.autonomy_decision import AutonomyMode
        mock_settings.BILGEAPI_AUTONOMY_MODE = AutonomyMode.SAFE_AUTONOMY
        mock_arbiter.execute_debate = AsyncMock(return_value=(True, {}))
        
        processed = await queue.process_next(context="test_worker")
        
        assert processed is not None
        assert processed["task_id"] == "t_crit"
        assert processed["status"] == "BLOCKED"

@pytest.mark.asyncio
async def test_consensus_veto_flow(mock_db):
    queue = AgentOrchestrationQueue()
    
    # Medium risk task
    await queue.enqueue(
        task_id="t_medium",
        source="system",
        agent_role="security",
        action_type="health_recheck",
        risk_level="medium"
    )
    
    # Mock settings and ConsensusArbiter to veto the task
    with patch("apps.bilgeapi.services.autonomy_decision.settings") as mock_settings, \
         patch("services.orchestration.application.agent_queue.consensus_arbiter") as mock_arbiter:
        from apps.bilgeapi.services.autonomy_decision import AutonomyMode
        mock_settings.BILGEAPI_AUTONOMY_MODE = AutonomyMode.SAFE_AUTONOMY
        
        # Mock consensus veto
        mock_arbiter.execute_debate = AsyncMock(return_value=(False, {"error": "VETOED"}))
        
        processed = await queue.process_next(context="test_worker")
        
        assert processed is not None
        assert processed["task_id"] == "t_medium"
        assert processed["status"] == "BLOCKED_CONSENSUS_VETO"

@pytest.mark.asyncio
async def test_stuck_task_dead_letter(mock_db):
    queue = AgentOrchestrationQueue()
    
    # Enqueue task
    await queue.enqueue(
        task_id="t_stuck",
        source="system",
        agent_role="general",
        action_type="clear_local_cache",
        risk_level="low",
        max_attempts=2
    )
    
    async with mock_db() as db:
        # Simulate failed attempts directly in DB
        res = await db.execute(select(AgentTaskQueueModel).where(AgentTaskQueueModel.task_id == "t_stuck"))
        task = res.scalar_one()
        task.attempt_count = 2 # Max attempts is 2, so the next attempt (3rd) should dead letter
        await db.commit()
        
    processed = await queue.process_next(context="test_worker")
    assert processed is not None
    assert processed["task_id"] == "t_stuck"
    assert processed["status"] == "DEAD_LETTER"

@pytest.mark.asyncio
async def test_lease_expiry_retry(mock_db):
    queue = AgentOrchestrationQueue()
    
    # Enqueue task
    await queue.enqueue(
        task_id="t_lease",
        source="system",
        agent_role="planner",
        action_type="clear_local_cache",
        risk_level="low"
    )
    
    # Lease the task manually in DB and expire the lease
    async with mock_db() as db:
        res = await db.execute(select(AgentTaskQueueModel).where(AgentTaskQueueModel.task_id == "t_lease"))
        task = res.scalar_one()
        task.status = "LEASED"
        
        lease = AgentTaskLeaseModel(
            task_id="t_lease",
            lease_owner="someone_else",
            lease_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1) # Expired!
        )
        db.add(lease)
        await db.commit()
        
    # Process the task (should detect expired lease and retry/acquire it)
    with patch("apps.bilgeapi.services.autonomy_decision.settings") as mock_settings:
        from apps.bilgeapi.services.autonomy_decision import AutonomyMode
        mock_settings.BILGEAPI_AUTONOMY_MODE = AutonomyMode.SAFE_AUTONOMY
        
        processed = await queue.process_next(context="test_worker")
        
        assert processed is not None
        assert processed["task_id"] == "t_lease"
        assert processed["status"] == "COMPLETED"
