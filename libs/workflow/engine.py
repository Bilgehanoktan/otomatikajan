import asyncio
import logging
from datetime import datetime
from typing import Callable, Any, Dict, Awaitable

from libs.workflow.models import WorkflowInstance, WorkflowStep, StepStatus, WorkflowStatus
from libs.workflow.persistence import WorkflowPersistence

logger = logging.getLogger("libs.workflow.engine")


class WorkflowEngine:
    def __init__(self):
        self.persistence = WorkflowPersistence()
        self._registry: Dict[str, Callable[..., Awaitable[Any]]] = {}

    def register_action(self, name: str, func: Callable[..., Awaitable[Any]]):
        """Register an async action function by name."""
        self._registry[name] = func
        logger.debug(f"Action registered: {name}")

    async def execute(self, instance: WorkflowInstance):
        """
        Executes a workflow instance using dependency-aware parallel scheduling.

        On each iteration:
        1. Find all PENDING steps whose dependencies are fully COMPLETED.
        2. Run them in parallel via asyncio.gather.
        3. Persist state and loop until terminal state or deadlock.
        """
        if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            logger.info(f"Workflow {instance.id} already finished ({instance.status}).")
            return

        instance.status = WorkflowStatus.RUNNING
        instance.started_at = instance.started_at or datetime.utcnow()
        await self.persistence.save_instance(instance)

        try:
            while instance.status == WorkflowStatus.RUNNING:
                completed_ids = {
                    s.id for s in instance.steps
                    if s.status == StepStatus.COMPLETED
                }

                # Steps that are PENDING and have all deps satisfied
                ready_steps = [
                    s for s in instance.steps
                    if s.status == StepStatus.PENDING
                    and all(dep_id in completed_ids for dep_id in s.dependencies)
                ]

                if not ready_steps:
                    # No more runnable steps — determine terminal state
                    all_terminal = all(
                        s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
                        for s in instance.steps
                    )
                    has_failure = any(s.status == StepStatus.FAILED for s in instance.steps)

                    if all_terminal:
                        instance.status = WorkflowStatus.COMPLETED
                    elif has_failure:
                        instance.status = WorkflowStatus.FAILED
                    else:
                        # Deadlock or unexpected state — fail safely
                        logger.error(
                            f"Workflow {instance.id} deadlocked. "
                            f"Steps: {[(s.id, s.status) for s in instance.steps]}"
                        )
                        instance.status = WorkflowStatus.FAILED
                    break

                logger.info(
                    f"[Workflow {instance.id}] Running {len(ready_steps)} steps in parallel: "
                    f"{[s.name for s in ready_steps]}"
                )
                await asyncio.gather(
                    *[self._execute_step(instance, step) for step in ready_steps]
                )

                # Persist shared context after each parallel batch
                await self.persistence.save_instance(instance)

                # If any step set instance to FAILED, stop the loop
                if instance.status == WorkflowStatus.FAILED:
                    break

            # Finalize
            instance.completed_at = datetime.utcnow()
            await self.persistence.save_instance(instance)
            logger.info(f"[Workflow {instance.id}] Terminal state: {instance.status}")

        except Exception as e:
            logger.critical(f"Workflow {instance.id} crashed: {e}", exc_info=True)
            instance.status = WorkflowStatus.FAILED
            try:
                await self.persistence.save_instance(instance)
            except Exception:
                pass

    async def _execute_step(self, instance: WorkflowInstance, step: WorkflowStep):
        """Execute a single step, with automatic retry on transient failures."""
        logger.info(f"[Step {step.name}] Starting action: {step.action}")
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()
        await self.persistence.save_step(instance.id, step)

        try:
            action_func = self._registry.get(step.action)
            if not action_func:
                raise ValueError(f"Action '{step.action}' not registered in WorkflowEngine")

            # Pass shared context + step-specific inputs
            result = await action_func(instance.context, **step.input_data)

            step.output_data = result if isinstance(result, dict) else {"result": result}
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow()

            # Allow steps to push updates into the shared context
            if isinstance(step.output_data, dict) and "_context_update" in step.output_data:
                instance.context.update(step.output_data["_context_update"])

            logger.info(f"[Step {step.name}] COMPLETED")

        except Exception as e:
            logger.error(f"[Step {step.name}] FAILED (attempt {step.retries + 1}): {e}")
            step.error = str(e)

            if step.retries < step.max_retries:
                # Retry: mark PENDING so it will be picked up in the next iteration
                step.retries += 1
                step.status = StepStatus.PENDING
                logger.info(f"[Step {step.name}] Scheduled for retry #{step.retries}")
            else:
                step.status = StepStatus.FAILED
                # Propagate failure to the workflow instance
                instance.status = WorkflowStatus.FAILED
                logger.error(f"[Step {step.name}] Max retries exceeded. Workflow FAILED.")

        await self.persistence.save_step(instance.id, step)
