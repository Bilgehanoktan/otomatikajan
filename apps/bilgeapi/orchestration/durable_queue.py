import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import select, delete, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from bilgeapi.models.database import AgentTaskQueueModel, AgentTaskLeaseModel, AgentOrchestrationRunModel

logger = logging.getLogger("bilgeapi.orchestration.durable_queue")


class DurableAgentQueue:
    """
    Database-backed durable task queue operating on the main system database.
    Guarantees at-least-once task execution and concurrency safety using unique lease locks.
    """

    def __init__(self, default_max_attempts: int = 3):
        self.default_max_attempts = default_max_attempts

    def _utcnow(self) -> datetime:
        return datetime.now(timezone.utc)

    async def enqueue_task(
        self,
        session: AsyncSession,
        agent_role: str,
        action_type: str,
        payload: Optional[Dict[str, Any]] = None,
        risk_level: str = "low",
        priority_score: float = 0.0,
        idempotency_key: Optional[str] = None,
        source: str = "system",
        max_attempts: Optional[int] = None
    ) -> AgentTaskQueueModel:
        """
        Enqueues a new task with PENDING status.
        Ensures idempotency if idempotency_key is provided.
        """
        now = self._utcnow()

        if idempotency_key:
            # Check for existing task with the same key
            stmt = select(AgentTaskQueueModel).where(AgentTaskQueueModel.idempotency_key == idempotency_key)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                logger.info(f"Task already exists for idempotency key '{idempotency_key}'. Returning task_id: {existing.task_id}")
                return existing

        task_id = f"task_{uuid.uuid4().hex[:12]}"
        max_att = max_attempts if max_attempts is not None else self.default_max_attempts

        task = AgentTaskQueueModel(
            task_id=task_id,
            source=source,
            agent_role=agent_role,
            action_type=action_type,
            payload=payload,
            risk_level=risk_level,
            priority_score=priority_score,
            status="PENDING",
            idempotency_key=idempotency_key,
            attempt_count=0,
            max_attempts=max_att,
            created_at=now,
            updated_at=now
        )
        session.add(task)
        await session.flush()
        
        logger.info(f"Successfully enqueued task '{task_id}' for agent role '{agent_role}'")
        return task

    async def acquire_next_task(
        self,
        session: AsyncSession,
        lease_owner: str,
        lease_duration_seconds: int = 120
    ) -> Optional[AgentTaskQueueModel]:
        """
        Finds the highest priority PENDING or stale RUNNING task and locks it.
        Uses database savepoints and transaction locks for concurrency safety.
        """
        now = self._utcnow()
        lease_expires_limit = now + timedelta(seconds=lease_duration_seconds)

        # 1. Fetch candidate tasks
        # Candidate 1: status is PENDING
        # Candidate 2: status is RUNNING but the associated lease has expired
        query = (
            select(AgentTaskQueueModel)
            .outerjoin(AgentTaskLeaseModel)
            .where(
                or_(
                    AgentTaskQueueModel.status == "PENDING",
                    and_(
                        AgentTaskQueueModel.status == "RUNNING",
                        or_(
                            AgentTaskLeaseModel.task_id.is_(None),  # Lease missing
                            AgentTaskLeaseModel.lease_expires_at < now  # Lease expired
                        )
                    )
                )
            )
            .order_by(
                AgentTaskQueueModel.priority_score.desc(),
                AgentTaskQueueModel.created_at.asc()
            )
            .limit(10)  # Scan up to 10 candidates
        )

        res = await session.execute(query)
        candidates = res.scalars().all()

        for task in candidates:
            # Try to lease candidate in a nested transaction (savepoint)
            try:
                async with session.begin_nested():
                    # Check if a lease already exists
                    lease_stmt = select(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == task.task_id)
                    lease_res = await session.execute(lease_stmt)
                    existing_lease = lease_res.scalar_one_or_none()

                    if existing_lease:
                        # Update existing expired lease
                        existing_lease.lease_owner = lease_owner
                        existing_lease.lease_expires_at = lease_expires_limit
                        existing_lease.acquired_at = now
                    else:
                        # Create new lease
                        new_lease = AgentTaskLeaseModel(
                            task_id=task.task_id,
                            lease_owner=lease_owner,
                            lease_expires_at=lease_expires_limit,
                            acquired_at=now
                        )
                        session.add(new_lease)

                    # Update task status and increment attempt
                    task.status = "RUNNING"
                    task.attempt_count += 1
                    task.updated_at = now
                    
                    await session.flush()
                
                # Nested transaction successfully committed (lease acquired)
                logger.info(f"Worker '{lease_owner}' successfully leased task '{task.task_id}' (attempt {task.attempt_count})")
                return task

            except IntegrityError:
                # Concurrency clash: another worker leased it first. Rollback to savepoint and try next.
                logger.debug(f"Conflict acquiring lease on task '{task.task_id}'. Retrying with next candidate.")
                continue

        return None

    async def complete_task(
        self,
        session: AsyncSession,
        task_id: str,
        execution_summary: Optional[str] = None,
        ledger_hash: Optional[str] = None
    ) -> None:
        """
        Marks task as COMPLETED, removes its lease, and records the run statistics.
        """
        now = self._utcnow()

        # Update task status
        stmt = (
            update(AgentTaskQueueModel)
            .where(AgentTaskQueueModel.task_id == task_id)
            .values(status="COMPLETED", updated_at=now)
        )
        await session.execute(stmt)

        # Delete the lease
        del_lease = delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == task_id)
        await session.execute(del_lease)

        # Create orchestration run record
        run = AgentOrchestrationRunModel(
            run_id=str(uuid.uuid4()),
            task_id=task_id,
            status="COMPLETED",
            execution_summary=execution_summary,
            evidence_ledger_hash=ledger_hash,
            started_at=now,
            completed_at=now
        )
        session.add(run)
        await session.flush()
        
        logger.info(f"Task '{task_id}' successfully marked COMPLETED")

    async def fail_task(
        self,
        session: AsyncSession,
        task_id: str,
        error_message: str
    ) -> None:
        """
        Fails the active task.
        If attempt_count < max_attempts, sets it back to PENDING. Otherwise sets it to FAILED.
        """
        now = self._utcnow()

        # Get task details
        stmt = select(AgentTaskQueueModel).where(AgentTaskQueueModel.task_id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()

        if not task:
            logger.warning(f"Attempted to fail non-existent task '{task_id}'")
            return

        # Delete lease
        del_lease = delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == task_id)
        await session.execute(del_lease)

        # Determine next status
        next_status = "PENDING"
        if task.attempt_count >= task.max_attempts:
            next_status = "FAILED"

        task.status = next_status
        task.updated_at = now

        # Record run
        run = AgentOrchestrationRunModel(
            run_id=str(uuid.uuid4()),
            task_id=task_id,
            status="FAILED",
            execution_summary=error_message,
            started_at=now,
            completed_at=now
        )
        session.add(run)
        await session.flush()

        logger.info(f"Task '{task_id}' failed (attempt {task.attempt_count}/{task.max_attempts}). Status: {next_status}")

    async def recover_stale_leases(self, session: AsyncSession) -> int:
        """
        Finds all expired leases, releases them, and marks associated tasks as PENDING or FAILED.
        """
        now = self._utcnow()

        # Query expired leases
        stmt = select(AgentTaskLeaseModel).where(AgentTaskLeaseModel.lease_expires_at < now)
        res = await session.execute(stmt)
        expired_leases = res.scalars().all()

        recovered_count = 0
        for lease in expired_leases:
            task_id = lease.task_id
            
            # Fetch task
            t_stmt = select(AgentTaskQueueModel).where(AgentTaskQueueModel.task_id == task_id)
            t_res = await session.execute(t_stmt)
            task = t_res.scalar_one_or_none()

            # Delete the lease
            await session.delete(lease)

            if task:
                # If attempt limit reached, mark FAILED, else PENDING
                if task.attempt_count >= task.max_attempts:
                    task.status = "FAILED"
                else:
                    task.status = "PENDING"
                task.updated_at = now
                
                # Log recovery run
                run = AgentOrchestrationRunModel(
                    run_id=str(uuid.uuid4()),
                    task_id=task_id,
                    status="RECOVERED_STALE",
                    execution_summary="Lease expired. Task recovered and reset.",
                    started_at=now,
                    completed_at=now
                )
                session.add(run)
                recovered_count += 1

        await session.flush()
        if recovered_count > 0:
            logger.info(f"Successfully recovered {recovered_count} stale/expired task leases")
        return recovered_count
