import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Callable, Optional, Set
from apps.bilgeapi.memory.db import get_workspace_db_session
from apps.bilgeapi.memory.repositories import AuditLogRepository, DecisionRepository
from apps.bilgeapi.orchestration.task_queue import TaskQueue
from apps.bilgeapi.security.secret_scanner import SecretScanner

logger = logging.getLogger("bilgeapi.orchestration.worker")

class TaskWorker:
    def __init__(
        self,
        workspace_dir: Path,
        task_queue: Optional[TaskQueue] = None,
        concurrency: int = 2,
        secret_scanner: Optional[SecretScanner] = None
    ):
        self.workspace_dir = Path(workspace_dir).resolve()
        self.task_queue = task_queue or TaskQueue()
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.secret_scanner = secret_scanner or SecretScanner()
        self.executors: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.active_tasks: Set[asyncio.Task] = set()
        self.running = False
        self.main_loop_task: Optional[asyncio.Task] = None

    def register_executor(self, action_type: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Registers an async handler function for a specific task action_type.
        """
        self.executors[action_type] = handler
        logger.info(f"Registered executor for action type: {action_type}")

    async def start(self) -> None:
        """
        Starts the worker background loop.
        """
        if self.running:
            return
        self.running = True
        self.main_loop_task = asyncio.create_task(self._run_loop())
        logger.info("TaskWorker background loop started.")

    async def stop(self, timeout: float = 10.0) -> None:
        """
        Gracefully stops the worker: stops pulling new tasks, waits for active tasks,
        and cancels any still running after timeout.
        """
        logger.info("Initiating graceful shutdown of TaskWorker...")
        self.running = False
        
        # Cancel main loop to stop pulling tasks
        if self.main_loop_task:
            self.main_loop_task.cancel()
            try:
                await self.main_loop_task
            except asyncio.CancelledError:
                pass

        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete (timeout={timeout}s)...")
            done, pending = await asyncio.wait(list(self.active_tasks), timeout=timeout)
            
            if pending:
                logger.warning(f"{len(pending)} tasks failed to complete within timeout. Cancelling them...")
                for task in pending:
                    task.cancel()
                
                # Gather exceptions/cancellations to clean them up
                await asyncio.gather(*pending, return_exceptions=True)

        logger.info("TaskWorker shutdown complete.")

    async def _run_loop(self) -> None:
        """
        Continuous loop polling the TaskQueue and spawning tasks when concurrency permits.
        """
        while self.running:
            try:
                # Wait until concurrency semaphore allows pulling a task
                await self.semaphore.acquire()
                
                task_dict = None
                async with get_workspace_db_session(self.workspace_dir) as session:
                    task_dict = await self.task_queue.dequeue(session)
                
                if not task_dict:
                    # No tasks available, release semaphore and back off
                    self.semaphore.release()
                    await asyncio.sleep(1.0)
                    continue

                # Spawn task execution asynchronously
                exec_task = asyncio.create_task(self._execute_task_wrapper(task_dict))
                self.active_tasks.add(exec_task)
                exec_task.add_done_callback(self._on_task_done)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in TaskWorker main loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    def _on_task_done(self, task: asyncio.Task) -> None:
        """
        Cleanup callback invoked when an execution task finishes.
        """
        self.active_tasks.discard(task)
        self.semaphore.release()

    async def _execute_task_wrapper(self, task: Dict[str, Any]) -> None:
        """
        Wraps task handler execution, performs error redaction, logging, and status transitions.
        """
        task_id = task["id"]
        action_type = task["action_type"]
        agent_role = task["agent_role"]
        risk_level = task["risk_level"]

        tenant_id = task.get("tenant_id") or "default"
        try:
            # 1. Action type registry check
            if action_type not in self.executors:
                logger.error(f"Unknown action_type '{action_type}' for task {task_id}.")
                reason_msg = f"Unknown or unregistered action_type: {action_type}"
                
                # Update task to FAILED using a new session
                async with get_workspace_db_session(self.workspace_dir) as session:
                    audit_repo = AuditLogRepository(session)
                    dec_repo = DecisionRepository(session)
                    
                    # Log transition: denied/failed due to registration
                    await audit_repo.log_audit(
                        tenant_id=tenant_id,
                        event_type="UNREGISTERED_ACTION_DENIED",
                        actor_id="orchestrator",
                        actor_type="SYSTEM",
                        action="EXECUTE",
                        target=f"task:{task_id}",
                        status="DENIED",
                        risk_level=risk_level,
                        before_state={"action_type": action_type},
                        after_state={"status": "FAILED"}
                    )
                    
                    await dec_repo.record_decision(
                        tenant_id=tenant_id,
                        task_id=task_id,
                        classification="UNREGISTERED_ACTION",
                        risk_score=9.0,
                        risk_level=risk_level,
                        eligibility="DENIED",
                        requires_human_gate=False,
                        decision_reason=reason_msg,
                        reasons=["Action is not in the allowed worker executors registry"]
                    )
                    
                    # Update status
                    await self.task_queue.fail_task(task_id, reason_msg, session, force_fail=True)
                return

            # 2. Get handler and execute
            handler = self.executors[action_type]
            
            # Execute handler (must be an async callable)
            if asyncio.iscoroutinefunction(handler):
                result = await handler(task)
            else:
                result = handler(task)

            # Redact secrets in execution results before logging
            clean_result = self.secret_scanner.scan_and_mask(str(result)) if result is not None else None

            # Mark task as completed
            async with get_workspace_db_session(self.workspace_dir) as session:
                await self.task_queue.complete_task(task_id, session)

        except asyncio.CancelledError:
            # Handle worker shutdown cancellation
            logger.warning(f"Task {task_id} cancelled during worker shutdown.")
            try:
                async with get_workspace_db_session(self.workspace_dir) as session:
                    await self.task_queue.fail_task(
                        task_id, "Task execution cancelled due to worker shutdown", session
                    )
            except Exception as e:
                logger.error(f"Failed to record cancellation for task {task_id}: {e}")
            raise

        except Exception as e:
            # Capture error message and redact secrets
            err_msg = str(e)
            clean_error = self.secret_scanner.scan_and_mask(err_msg)
            logger.error(f"Error executing task {task_id}: {clean_error}")

            async with get_workspace_db_session(self.workspace_dir) as session:
                await self.task_queue.fail_task(task_id, clean_error, session)
