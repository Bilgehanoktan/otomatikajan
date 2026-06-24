import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bilgeapi.memory.models import TaskModel
from apps.bilgeapi.memory.repositories import TaskRepository, AuditLogRepository, DecisionRepository
from apps.bilgeapi.orchestration.retry_policy import RetryPolicy

logger = logging.getLogger("bilgeapi.orchestration.task_queue")

def _to_dict(model_obj) -> Optional[Dict[str, Any]]:
    if not model_obj:
        return None
    res = {}
    for col in model_obj.__table__.columns:
        val = getattr(model_obj, col.name)
        if isinstance(val, datetime):
            res[col.name] = val.isoformat()
        else:
            res[col.name] = val
    return res

class TaskQueue:
    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()

    def _get_next_run_time(self, task: Dict[str, Any]) -> datetime:
        """
        Calculates when the task is scheduled to run next.
        Structured to easily adapt to a future 'next_run_at' column.
        """
        # Feature flag check for future schema support
        if "next_run_at" in task and task["next_run_at"]:
            val = task["next_run_at"]
            if isinstance(val, str):
                return datetime.fromisoformat(val)
            return val
        
        # MVP logic: updated_at + backoff_delay
        attempt_count = task.get("attempt_count", 0)
        if attempt_count == 0:
            updated_at = task.get("updated_at")
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at)
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            return updated_at

        delay_seconds = self.retry_policy.get_backoff_delay(attempt_count)
        updated_at = task.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        return updated_at + timedelta(seconds=delay_seconds)

    async def enqueue(
        self,
        system_id: str,
        title: str,
        agent_role: str,
        action_type: str,
        risk_level: str,
        payload: Optional[Dict[str, Any]],
        session: AsyncSession,
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Enqueues a new task and logs the task creation.
        """
        task_repo = TaskRepository(session)
        audit_repo = AuditLogRepository(session)
        dec_repo = DecisionRepository(session)

        # Create the task (default status is PENDING)
        task = await task_repo.create_task(
            tenant_id=tenant_id,
            system_id=system_id,
            title=title,
            description=None,
            agent_role=agent_role,
            action_type=action_type,
            status="PENDING",
            risk_level=risk_level,
            payload=payload
        )

        task_id = task["id"]

        # Log transition: task created
        await audit_repo.log_audit(
            tenant_id=tenant_id,
            event_type="TASK_CREATED",
            actor_id=agent_role,
            actor_type="AI_AGENT",
            action="CREATE",
            target=f"task:{task_id}",
            status="ALLOWED",
            risk_level=risk_level,
            before_state=None,
            after_state={"task_id": task_id, "status": "PENDING"}
        )

        await dec_repo.record_decision(
            tenant_id=tenant_id,
            task_id=task_id,
            classification="TASK_ENQUEUE",
            risk_score=1.0,
            risk_level=risk_level,
            eligibility="ELIGIBLE",
            requires_human_gate=False,
            decision_reason="Task enqueued successfully into orchestration queue",
            reasons=["Initial queue placement"]
        )

        return task

    async def dequeue(self, session: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Atomically claims the next eligible task (status in PENDING, PENDING_APPROVED)
        taking retry backoff into account. Uses optimistic locking for SQLite concurrency safety.
        """
        audit_repo = AuditLogRepository(session)
        dec_repo = DecisionRepository(session)

        # 1. Fetch all candidate tasks
        stmt = select(TaskModel).where(
            TaskModel.status.in_(["PENDING", "PENDING_APPROVED"])
        ).order_by(TaskModel.created_at.asc())
        
        res = await session.execute(stmt)
        candidates = res.scalars().all()
        
        now = datetime.now(timezone.utc)

        for candidate in candidates:
            cand_dict = _to_dict(candidate)
            
            # Check if retry backoff has elapsed
            next_run = self._get_next_run_time(cand_dict)
            if now < next_run:
                # Still backing off
                continue

            # Eligible! Try to atomically update status to RUNNING
            # where current status matches the read status (Optimistic locking status transition)
            upd_stmt = update(TaskModel).where(
                TaskModel.id == candidate.id,
                TaskModel.status == candidate.status
            ).values(
                status="RUNNING",
                attempt_count=TaskModel.attempt_count + 1,
                updated_at=now
            )
            
            upd_res = await session.execute(upd_stmt)
            if upd_res.rowcount == 1:
                # Claimed successfully! Refresh to get updated values
                await session.flush()
                
                # Fetch updated task
                stmt_ref = select(TaskModel).where(TaskModel.id == candidate.id)
                task_obj = (await session.execute(stmt_ref)).scalar_one()
                task_dict = _to_dict(task_obj)
                
                task_id = task_dict["id"]
                risk_level = task_dict["risk_level"]
                tenant_id = task_dict.get("tenant_id") or "default"
                
                # Log transition: dequeued / running
                await audit_repo.log_audit(
                    tenant_id=tenant_id,
                    event_type="TASK_DEQUEUED",
                    actor_id="orchestrator",
                    actor_type="SYSTEM",
                    action="DEQUEUE",
                    target=f"task:{task_id}",
                    status="ALLOWED",
                    risk_level=risk_level,
                    before_state={"status": candidate.status},
                    after_state={"status": "RUNNING", "attempt_count": task_dict["attempt_count"]}
                )

                await dec_repo.record_decision(
                    tenant_id=tenant_id,
                    task_id=task_id,
                    classification="TASK_DEQUEUE",
                    risk_score=2.0,
                    risk_level=risk_level,
                    eligibility="DEQUEUED",
                    requires_human_gate=False,
                    decision_reason="Task claimed and transitioned to RUNNING state",
                    reasons=[f"Claimed from state: {candidate.status}"]
                )

                # Commit right away to make it visible to other sessions
                await session.commit()
                return task_dict

        return None

    async def complete_task(self, task_id: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Marks task as COMPLETED.
        """
        task_repo = TaskRepository(session)
        audit_repo = AuditLogRepository(session)
        dec_repo = DecisionRepository(session)

        # Get task directly from session to obtain its tenant_id
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        res = await session.execute(stmt)
        db_task = res.scalar_one_or_none()
        if not db_task:
            raise ValueError(f"Task {task_id} not found")
        tenant_id = db_task.tenant_id or "default"
        task = _to_dict(db_task)

        updated_task = await task_repo.update_task_status(tenant_id, task_id, "COMPLETED")
        
        # Log transition: completed
        await audit_repo.log_audit(
            tenant_id=tenant_id,
            event_type="TASK_COMPLETED",
            actor_id="orchestrator",
            actor_type="SYSTEM",
            action="COMPLETE",
            target=f"task:{task_id}",
            status="ALLOWED",
            risk_level=task["risk_level"],
            before_state={"status": task["status"]},
            after_state={"status": "COMPLETED"}
        )

        await dec_repo.record_decision(
            tenant_id=tenant_id,
            task_id=task_id,
            classification="TASK_COMPLETE",
            risk_score=1.0,
            risk_level=task["risk_level"],
            eligibility="COMPLETED",
            requires_human_gate=False,
            decision_reason="Task executed successfully and completed",
            reasons=["Successful execution"]
        )

        await session.commit()
        return updated_task

    async def fail_task(self, task_id: str, error_msg: str, session: AsyncSession, force_fail: bool = False) -> Dict[str, Any]:
        """
        Marks task as FAILED or PENDING (for retry) depending on RetryPolicy.
        """
        task_repo = TaskRepository(session)
        audit_repo = AuditLogRepository(session)
        dec_repo = DecisionRepository(session)

        # Get task directly from session to obtain its tenant_id
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        res = await session.execute(stmt)
        db_task = res.scalar_one_or_none()
        if not db_task:
            raise ValueError(f"Task {task_id} not found")
        tenant_id = db_task.tenant_id or "default"
        task = _to_dict(db_task)

        # Determine if we should retry
        if not force_fail and self.retry_policy.should_retry(task):
            # Retry scheduled: status goes back to PENDING
            updated_task = await task_repo.update_task_status(tenant_id, task_id, "PENDING")
            
            # Log transition: retry scheduled
            await audit_repo.log_audit(
                tenant_id=tenant_id,
                event_type="TASK_RETRY_SCHEDULED",
                actor_id="orchestrator",
                actor_type="SYSTEM",
                action="RETRY",
                target=f"task:{task_id}",
                status="ALLOWED",
                risk_level=task["risk_level"],
                before_state={"status": "RUNNING", "error": error_msg},
                after_state={"status": "PENDING", "attempt": updated_task["attempt_count"]}
            )

            await dec_repo.record_decision(
                tenant_id=tenant_id,
                task_id=task_id,
                classification="TASK_RETRY",
                risk_score=3.0,
                risk_level=task["risk_level"],
                eligibility="RETRYABLE",
                requires_human_gate=False,
                decision_reason=f"Task execution failed: {error_msg}. Retry scheduled.",
                reasons=[f"Attempt {updated_task['attempt_count']} failed"]
            )
        else:
            # Permanently failed
            updated_task = await task_repo.update_task_status(tenant_id, task_id, "FAILED")
            
            # Log transition: permanently failed
            await audit_repo.log_audit(
                tenant_id=tenant_id,
                event_type="TASK_PERMANENTLY_FAILED",
                actor_id="orchestrator",
                actor_type="SYSTEM",
                action="FAIL",
                target=f"task:{task_id}",
                status="DENIED",
                risk_level=task["risk_level"],
                before_state={"status": "RUNNING", "error": error_msg},
                after_state={"status": "FAILED"}
            )

            await dec_repo.record_decision(
                tenant_id=tenant_id,
                task_id=task_id,
                classification="TASK_FAIL",
                risk_score=5.0,
                risk_level=task["risk_level"],
                eligibility="FAILED",
                requires_human_gate=False,
                decision_reason=f"Task execution failed permanently: {error_msg}. Retry limit exceeded.",
                reasons=["Max retries reached"]
            )

        await session.commit()
        return updated_task

    async def block_task(self, task_id: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Marks task as BLOCKED (e.g. when human approval is required).
        """
        task_repo = TaskRepository(session)
        audit_repo = AuditLogRepository(session)
        dec_repo = DecisionRepository(session)

        # Get task directly from session to obtain its tenant_id
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        res = await session.execute(stmt)
        db_task = res.scalar_one_or_none()
        if not db_task:
            raise ValueError(f"Task {task_id} not found")
        tenant_id = db_task.tenant_id or "default"
        task = _to_dict(db_task)

        updated_task = await task_repo.update_task_status(tenant_id, task_id, "BLOCKED")
        
        # Log transition: blocked
        await audit_repo.log_audit(
            tenant_id=tenant_id,
            event_type="TASK_BLOCKED",
            actor_id="orchestrator",
            actor_type="SYSTEM",
            action="BLOCK",
            target=f"task:{task_id}",
            status="DENIED",
            risk_level=task["risk_level"],
            before_state={"status": task["status"]},
            after_state={"status": "BLOCKED"}
        )

        await dec_repo.record_decision(
            tenant_id=tenant_id,
            task_id=task_id,
            classification="TASK_BLOCK",
            risk_score=4.0,
            risk_level=task["risk_level"],
            eligibility="BLOCKED",
            requires_human_gate=True,
            decision_reason="Task requires human gate / approval and has been blocked",
            reasons=["Human approval required"]
        )

        await session.commit()
        return updated_task

    async def recover_stale_tasks(self, timeout_seconds: float, session: AsyncSession) -> int:
        """
        Recovers tasks that have been in RUNNING status longer than timeout_seconds.
        Transitions them using fail_task.
        """
        stmt = select(TaskModel).where(TaskModel.status == "RUNNING")
        res = await session.execute(stmt)
        running_tasks = res.scalars().all()
        
        now = datetime.now(timezone.utc)
        recovered_count = 0

        for r_task in running_tasks:
            updated_at = r_task.updated_at
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)

            delta = now - updated_at
            if delta.total_seconds() > timeout_seconds:
                logger.warning(f"Task {r_task.id} has been running for {delta.total_seconds()}s (timeout={timeout_seconds}s). Recovering...")
                await self.fail_task(r_task.id, "Task timed out (stale task recovery)", session)
                recovered_count += 1

        return recovered_count
