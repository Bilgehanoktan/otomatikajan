"""
libs/workflow/engine.py — Phase 13.04
Dependency-aware parallel WorkflowEngine with OTel distributed tracing.

Every workflow execution creates a root span.
Every step creates a child span with step metadata as attributes.
Trace IDs propagate to logs via correlation_id().
"""
import asyncio
import logging
from datetime import datetime
from typing import Callable, Any, Dict, Awaitable

from libs.workflow.models import WorkflowInstance, WorkflowStep, StepStatus, WorkflowStatus
from libs.workflow.persistence import WorkflowPersistence

# OTel — soft dependency (never crashes if not installed)
try:
    from libs.observability.tracer import span as _otel_span, set_span_attrs, add_span_event
    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False
    from contextlib import contextmanager

    @contextmanager
    def _otel_span(*a, **kw):
        yield type("_NoOp", (), {"set_attribute": lambda *a, **kw: None})()

    def set_span_attrs(**kw): pass
    def add_span_event(name, **kw): pass

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
        Creates an OTel root span wrapping the entire workflow.

        On each iteration:
        1. Find all PENDING steps whose dependencies are fully COMPLETED.
        2. Run them in parallel via asyncio.gather.
        3. Persist state and loop until terminal state or deadlock.
        """
        if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            logger.info(f"Workflow {instance.id} already finished ({instance.status}).")
            return

        span_attrs = {
            "workflow.id":   str(instance.id),
            "workflow.type": instance.workflow_type,
            "workflow.steps": len(instance.steps),
        }

        async def _run():
            instance.status = WorkflowStatus.RUNNING
            instance.started_at = instance.started_at or datetime.utcnow()
            await self.persistence.save_instance(instance)

            try:
                while instance.status == WorkflowStatus.RUNNING:
                    completed_ids = {
                        s.id for s in instance.steps
                        if s.status == StepStatus.COMPLETED
                    }

                    ready_steps = [
                        s for s in instance.steps
                        if s.status == StepStatus.PENDING
                        and all(dep_id in completed_ids for dep_id in s.dependencies)
                    ]

                    if not ready_steps:
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
                            pending = [(s.id, s.status) for s in instance.steps if s.status not in (StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.FAILED)]
                            logger.error(
                                f"Workflow {instance.id} deadlocked. "
                                f"Steps: {[(s.id, s.status) for s in instance.steps]}"
                            )
                            add_span_event("workflow.deadlock", {"pending_steps": str(pending)})
                            instance.status = WorkflowStatus.FAILED
                        break

                    step_names = [s.name for s in ready_steps]
                    logger.info(
                        f"[Workflow {instance.id}] Running {len(ready_steps)} steps in parallel: "
                        f"{step_names}"
                    )
                    add_span_event("workflow.batch_start", {"steps": str(step_names)})

                    await asyncio.gather(
                        *[self._execute_step(instance, step) for step in ready_steps]
                    )

                    await self.persistence.save_instance(instance)

                    if instance.status == WorkflowStatus.FAILED:
                        break

                instance.completed_at = datetime.utcnow()
                await self.persistence.save_instance(instance)

                set_span_attrs(
                    **{
                        "workflow.final_status": instance.status.value,
                        "workflow.completed_steps": sum(1 for s in instance.steps if s.status == StepStatus.COMPLETED),
                        "workflow.failed_steps":    sum(1 for s in instance.steps if s.status == StepStatus.FAILED),
                    }
                )
                logger.info(f"[Workflow {instance.id}] Terminal state: {instance.status}")

            except Exception as e:
                logger.critical(f"Workflow {instance.id} crashed: {e}", exc_info=True)
                instance.status = WorkflowStatus.FAILED
                try:
                    await self.persistence.save_instance(instance)
                except Exception:
                    pass
                raise

        # Wrap entire workflow in an OTel span
        with _otel_span("workflow.execute", attributes=span_attrs):
            await _run()

    async def _execute_step(self, instance: WorkflowInstance, step: WorkflowStep):
        """Execute a single step with retry, wrapped in its own OTel child span."""
        step_attrs = {
            "step.id":           str(step.id),
            "step.name":         step.name,
            "step.action":       step.action,
            "step.max_retries":  step.max_retries,
            "workflow.id":       str(instance.id),
        }

        async def _run_step():
            logger.info(f"[Step {step.name}] Starting action: {step.action}")
            step.status = StepStatus.RUNNING
            step.started_at = datetime.utcnow()
            await self.persistence.save_step(instance.id, step)

            try:
                action_func = self._registry.get(step.action)
                if not action_func:
                    raise ValueError(f"Action '{step.action}' not registered in WorkflowEngine")

                result = await action_func(instance.context, **step.input_data)

                step.output_data = result if isinstance(result, dict) else {"result": result}
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.utcnow()

                if isinstance(step.output_data, dict) and "_context_update" in step.output_data:
                    instance.context.update(step.output_data["_context_update"])

                set_span_attrs(**{
                    "step.status":  "completed",
                    "step.retries": step.retries,
                })
                logger.info(f"[Step {step.name}] COMPLETED")

            except Exception as e:
                logger.error(f"[Step {step.name}] FAILED (attempt {step.retries + 1}): {e}")
                step.error = str(e)
                add_span_event("step.error", {"error": str(e), "attempt": step.retries + 1})

                if step.retries < step.max_retries:
                    step.retries += 1
                    step.status = StepStatus.PENDING
                    logger.info(f"[Step {step.name}] Scheduled for retry #{step.retries}")
                else:
                    step.status = StepStatus.FAILED
                    instance.status = WorkflowStatus.FAILED
                    set_span_attrs(**{"step.status": "failed", "step.error": str(e)})
                    logger.error(f"[Step {step.name}] Max retries exceeded. Workflow FAILED.")

            await self.persistence.save_step(instance.id, step)

        with _otel_span(f"step.{step.action}", attributes=step_attrs):
            await _run_step()
