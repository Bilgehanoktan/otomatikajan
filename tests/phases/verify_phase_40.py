import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from libs.db.base import Base
from apps.bilgeapi.models.database import (
    AgentTaskQueueModel,
    AgentTaskLeaseModel,
    AgentOrchestrationRunModel
)
from services.orchestration.application.agent_queue import AgentOrchestrationQueue

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("phase_40_verif")

async def test_durable_agent_queue_flow() -> bool:
    _log.info("Starting Phase 40 Verification: Durable Agent Orchestration Queue...")
    
    # 1. Setup in-memory SQLite DB
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    @asynccontextmanager
    async def mock_session_scope():
        async with async_session() as session:
            yield session
            
    # Mock session_scope and kinetic_arbiter globally for the test run
    with patch("services.orchestration.application.agent_queue.session_scope", mock_session_scope), \
         patch("services.orchestration.application.agent_queue.kinetic_arbiter") as mock_arbiter:
         
        mock_arbiter.acquire_slot = AsyncMock(return_value=True)
        mock_arbiter.release_slot = MagicMock()
        
        queue = AgentOrchestrationQueue()
        
        # Scenario A: Enqueue and process a low-risk safe task (clear_local_cache)
        _log.info("[*] Scenario A: Processing low-risk safe task...")
        t_low = await queue.enqueue(
            task_id="verif_low",
            source="system",
            agent_role="planner",
            action_type="clear_local_cache",
            risk_level="low"
        )
        
        if t_low["status"] != "PENDING":
            _log.error("FAILURE: Enqueued low-risk task status is not PENDING.")
            return False
            
        with patch("apps.bilgeapi.services.autonomy_decision.settings") as mock_settings:
            from apps.bilgeapi.services.autonomy_decision import AutonomyMode
            mock_settings.BILGEAPI_AUTONOMY_MODE = AutonomyMode.SAFE_AUTONOMY
            
            processed = await queue.process_next(context="verif_worker")
            if not processed or processed["status"] != "COMPLETED":
                _log.error("FAILURE: Low-risk safe task did not transition to COMPLETED.")
                return False
                
        # Check database persistence for the run
        async with async_session() as db:
            res = await db.execute(select(AgentOrchestrationRunModel).where(AgentOrchestrationRunModel.task_id == "verif_low"))
            run = res.scalar_one_or_none()
            if not run or run.status != "COMPLETED":
                _log.error("FAILURE: Run model was not correctly persisted in DB.")
                return False
        _log.info("✅ SUCCESS: Low-risk safe task auto-run verified.")

        # Scenario B: High-risk task requires human gate
        _log.info("[*] Scenario B: Processing high-risk task (gate mapping)...")
        await queue.enqueue(
            task_id="verif_high",
            source="system",
            agent_role="devops",
            action_type="sandbox_retry", # Score 50 (severity high) + 10 = 60 (HIGH risk)
            risk_level="high"
        )
        
        with patch("apps.bilgeapi.services.autonomy_decision.settings") as mock_settings, \
             patch("services.orchestration.application.agent_queue.consensus_arbiter") as mock_consensus:
             
            mock_settings.BILGEAPI_AUTONOMY_MODE = AutonomyMode.SAFE_AUTONOMY
            mock_consensus.execute_debate = AsyncMock(return_value=(True, {}))
            
            processed = await queue.process_next(context="verif_worker")
            if not processed or processed["status"] != "HUMAN_GATE_REQUIRED":
                _log.error(f"FAILURE: High-risk task status is {processed['status'] if processed else None}, expected HUMAN_GATE_REQUIRED.")
                return False
        _log.info("✅ SUCCESS: High-risk task routed to human gate.")

        # Scenario C: Consensus veto routes to BLOCKED_CONSENSUS_VETO
        _log.info("[*] Scenario C: Processing task with consensus veto...")
        await queue.enqueue(
            task_id="verif_veto",
            source="system",
            agent_role="security",
            action_type="sandbox_retry",
            risk_level="medium"
        )
        
        with patch("apps.bilgeapi.services.autonomy_decision.settings") as mock_settings, \
             patch("services.orchestration.application.agent_queue.consensus_arbiter") as mock_consensus:
             
            mock_settings.BILGEAPI_AUTONOMY_MODE = AutonomyMode.SAFE_AUTONOMY
            mock_consensus.execute_debate = AsyncMock(return_value=(False, {"error": "VETOED_BY_VERIFIER"}))
            
            processed = await queue.process_next(context="verif_worker")
            if not processed or processed["status"] != "BLOCKED_CONSENSUS_VETO":
                _log.error(f"FAILURE: Vetoed task status is {processed['status'] if processed else None}, expected BLOCKED_CONSENSUS_VETO.")
                return False
        _log.info("✅ SUCCESS: Consensus veto correctly blocked task.")

    _log.info("Phase 40 Verification COMPLETED.")
    return True

if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(test_durable_agent_queue_flow()) else 1)
