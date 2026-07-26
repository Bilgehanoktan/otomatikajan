import logging
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bilgeapi.orchestration.durable_queue import DurableAgentQueue
from bilgeapi.models.database import AgentTaskQueueModel

logger = logging.getLogger("bilgeapi.services.ceo_orchestrator")


class CEOOrcAgent:
    """
    Orchestrates the multi-agent incident resolution lifecycle.
    Manages state transitions and dispatches sub-tasks to Analyst, Security, Tester, Repair, and Reviewer agents.
    """

    def __init__(self, queue: DurableAgentQueue):
        self.queue = queue

    async def initialize_resolution(
        self,
        session: AsyncSession,
        incident_id: str,
        source: str = "system"
    ) -> str:
        """
        Starts the resolution process by creating a root CEO_AGENT task.
        """
        payload = {
            "incident_id": incident_id,
            "current_phase": "INIT",
            "analyst_task_id": None,
            "tester_task_id": None,
            "security_task_id": None,
            "repair_task_id": None,
            "reviewer_task_id": None
        }

        task = await self.queue.enqueue_task(
            session=session,
            agent_role="CEO_AGENT",
            action_type="ORCHESTRATE_RESOLVE",
            payload=payload,
            risk_level="low",
            priority_score=10.0,
            idempotency_key=f"ceo_resolve_{incident_id}",
            source=source
        )
        return task.task_id

    async def orchestrate_next_step(
        self,
        session: AsyncSession,
        ceo_task_id: str
    ) -> Dict[str, Any]:
        """
        Drives the state machine for incident resolution.
        Reads sub-task statuses and enqueues next-phase agent tasks.
        """
        # Fetch current CEO task
        stmt = select(AgentTaskQueueModel).where(AgentTaskQueueModel.task_id == ceo_task_id)
        res = await session.execute(stmt)
        ceo_task = res.scalar_one_or_none()

        if not ceo_task:
            raise ValueError(f"CEO Task '{ceo_task_id}' not found")

        if ceo_task.status == "COMPLETED":
            return {"status": "COMPLETED", "phase": "DONE", "message": "Resolution already completed successfully."}
        if ceo_task.status == "FAILED":
            return {"status": "FAILED", "phase": "FAILED", "message": "Resolution process previously failed."}

        payload = ceo_task.payload or {}
        current_phase = payload.get("current_phase", "INIT")
        incident_id = payload.get("incident_id")

        if current_phase == "INIT":
            # 1. Enqueue Analyst Task
            analyst_task = await self.queue.enqueue_task(
                session=session,
                agent_role="ANALYST",
                action_type="ANALYZE_INCIDENT",
                payload={"incident_id": incident_id},
                risk_level="low",
                priority_score=9.0,
                idempotency_key=f"analyst_{incident_id}",
                source=ceo_task.source
            )
            payload["current_phase"] = "ANALYSIS"
            payload["analyst_task_id"] = analyst_task.task_id
            
            # Update CEO task payload
            ceo_task.payload = payload
            await session.flush()
            
            return {
                "status": "RUNNING",
                "phase": "ANALYSIS",
                "message": f"Dispatched Analyst task '{analyst_task.task_id}'"
            }

        elif current_phase == "ANALYSIS":
            # Check Analyst task status
            analyst_id = payload.get("analyst_task_id")
            analyst_status = await self._get_task_status(session, analyst_id)

            if analyst_status == "COMPLETED":
                # 2. Dispatch Tester and Security tasks
                tester_task = await self.queue.enqueue_task(
                    session=session,
                    agent_role="TESTER",
                    action_type="REPRODUCE_BUG",
                    payload={"incident_id": incident_id},
                    risk_level="medium",
                    priority_score=8.0,
                    idempotency_key=f"tester_{incident_id}",
                    source=ceo_task.source
                )
                security_task = await self.queue.enqueue_task(
                    session=session,
                    agent_role="SECURITY",
                    action_type="SECURITY_AUDIT",
                    payload={"incident_id": incident_id},
                    risk_level="low",
                    priority_score=8.0,
                    idempotency_key=f"security_{incident_id}",
                    source=ceo_task.source
                )

                payload["current_phase"] = "VERIFICATION"
                payload["tester_task_id"] = tester_task.task_id
                payload["security_task_id"] = security_task.task_id
                ceo_task.payload = payload
                await session.flush()

                return {
                    "status": "RUNNING",
                    "phase": "VERIFICATION",
                    "message": f"Analyst finished. Dispatched Tester '{tester_task.task_id}' and Security '{security_task.task_id}'"
                }
            elif analyst_status == "FAILED":
                await self.queue.fail_task(session, ceo_task_id, "Analyst sub-task failed")
                return {"status": "FAILED", "phase": "ANALYSIS", "message": "Analyst sub-task failed. Aborted."}
            else:
                return {"status": "RUNNING", "phase": "ANALYSIS", "message": "Waiting for Analyst sub-task to complete."}

        elif current_phase == "VERIFICATION":
            # Check both Verification tasks
            tester_id = payload.get("tester_task_id")
            security_id = payload.get("security_task_id")

            tester_status = await self._get_task_status(session, tester_id)
            security_status = await self._get_task_status(session, security_id)

            if tester_status == "COMPLETED" and security_status == "COMPLETED":
                # 3. Dispatch Repair Task
                repair_task = await self.queue.enqueue_task(
                    session=session,
                    agent_role="REPAIR",
                    action_type="PATCH_CODE",
                    payload={"incident_id": incident_id},
                    risk_level="high",
                    priority_score=7.0,
                    idempotency_key=f"repair_{incident_id}",
                    source=ceo_task.source
                )

                payload["current_phase"] = "REPAIR"
                payload["repair_task_id"] = repair_task.task_id
                ceo_task.payload = payload
                await session.flush()

                return {
                    "status": "RUNNING",
                    "phase": "REPAIR",
                    "message": f"Verification passed. Dispatched Repair task '{repair_task.task_id}'"
                }
            elif tester_status == "FAILED" or security_status == "FAILED":
                await self.queue.fail_task(session, ceo_task_id, f"Verification failed. Tester: {tester_status}, Security: {security_status}")
                return {"status": "FAILED", "phase": "VERIFICATION", "message": "Verification sub-tasks failed. Aborted."}
            else:
                return {"status": "RUNNING", "phase": "VERIFICATION", "message": "Waiting for Tester/Security sub-tasks to complete."}

        elif current_phase == "REPAIR":
            # Check Repair status
            repair_id = payload.get("repair_task_id")
            repair_status = await self._get_task_status(session, repair_id)

            if repair_status == "COMPLETED":
                # 4. Dispatch Review Task
                reviewer_task = await self.queue.enqueue_task(
                    session=session,
                    agent_role="REVIEWER",
                    action_type="CODE_REVIEW",
                    payload={"incident_id": incident_id},
                    risk_level="low",
                    priority_score=6.0,
                    idempotency_key=f"reviewer_{incident_id}",
                    source=ceo_task.source
                )

                payload["current_phase"] = "REVIEW"
                payload["reviewer_task_id"] = reviewer_task.task_id
                ceo_task.payload = payload
                await session.flush()

                return {
                    "status": "RUNNING",
                    "phase": "REVIEW",
                    "message": f"Repair completed. Dispatched Reviewer task '{reviewer_task.task_id}'"
                }
            elif repair_status == "FAILED":
                await self.queue.fail_task(session, ceo_task_id, "Repair sub-task failed")
                return {"status": "FAILED", "phase": "REPAIR", "message": "Repair sub-task failed. Aborted."}
            else:
                return {"status": "RUNNING", "phase": "REPAIR", "message": "Waiting for Repair sub-task to complete."}

        elif current_phase == "REVIEW":
            # Check Reviewer status
            reviewer_id = payload.get("reviewer_task_id")
            reviewer_status = await self._get_task_status(session, reviewer_id)

            if reviewer_status == "COMPLETED":
                # 5. Complete resolution!
                await self.queue.complete_task(session, ceo_task_id, execution_summary="Incident resolved successfully by multi-agent flow.")
                return {"status": "COMPLETED", "phase": "DONE", "message": "Resolution completed successfully."}
            elif reviewer_status == "FAILED":
                await self.queue.fail_task(session, ceo_task_id, "Reviewer sub-task failed")
                return {"status": "FAILED", "phase": "REVIEW", "message": "Reviewer sub-task failed. Aborted."}
            else:
                return {"status": "RUNNING", "phase": "REVIEW", "message": "Waiting for Reviewer sub-task to complete."}

        return {"status": "RUNNING", "phase": current_phase, "message": "Orchestrator processed step."}

    async def _get_task_status(self, session: AsyncSession, task_id: str) -> str:
        """Helper to get a task status from the DB."""
        if not task_id:
            return "PENDING"
        stmt = select(AgentTaskQueueModel.status).where(AgentTaskQueueModel.task_id == task_id)
        res = await session.execute(stmt)
        status = res.scalar_one_or_none()
        return status or "PENDING"
