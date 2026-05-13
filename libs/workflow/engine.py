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
from typing import Callable, Any, Dict, Awaitable, Optional

from libs.workflow.models import WorkflowInstance, WorkflowStep, StepStatus, WorkflowStatus
from libs.workflow.registry import WorkflowRegistry
from libs.workflow.persistence import WorkflowPersistence

# Phase 14: Governance Imports
from services.governance.autonomy_policy import autonomy_engine
from services.governance.cost_guard import cost_guard
from services.governance.approval_policy import approval_engine

from services.observability.logging import get_logger
try:
    from libs.observability.tracer import span as _otel_span, set_span_attrs, add_span_event, correlation_id
    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False
    from contextlib import contextmanager

    @contextmanager
    def _otel_span(*a, **kw):
        yield type("_NoOp", (), {"set_attribute": lambda *a, **kw: None})()

    def set_span_attrs(**kw): pass
    def add_span_event(name, attributes=None, **kw): pass
    def correlation_id(): return "no-otel"

logger = get_logger("libs.workflow.engine")

# WS — optional real-time broadcast
try:
    from libs.infra.ws_manager import ws_manager
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False


def _condition_value(value: str, context: dict[str, Any]) -> Any:
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return float(value)
    except ValueError:
        return context.get(value.strip())


def _condition_matches(condition: str | None, context: dict[str, Any]) -> bool:
    if not condition:
        return True
    # Phase 28: Simple expression parser for branching
    for operator in (">=", "<=", "==", ">", "<"):
        if operator in condition:
            left_raw, right_raw = condition.split(operator, 1)
            left = _condition_value(left_raw, context)
            right = _condition_value(right_raw, context)
            if operator == "==":
                return left == right
            try:
                left_number = float(left or 0)
                right_number = float(right or 0)
                if operator == ">=":
                    return left_number >= right_number
                if operator == "<=":
                    return left_number <= right_number
                if operator == ">":
                    return left_number > right_number
                if operator == "<":
                    return left_number < right_number
            except (ValueError, TypeError):
                return False
    return False


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
        1. Find all PENDING or REPLAY_PENDING steps whose dependencies are fully COMPLETED.
        2. Run them in parallel via asyncio.gather.
        3. Persist state and loop until terminal state or deadlock.
        """
        if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED] and instance.status != WorkflowStatus.REPLAYING:
            logger.info(f"Workflow {instance.id} in terminal state ({instance.status}). Skipping.")
            return

        span_attrs = {
            "workflow.id":   instance.id,
            "workflow.type": instance.workflow_type,
            "workflow.steps": len(instance.steps),
        }

        async def _run():
            nonlocal instance
            from datetime import timezone
            instance.status = WorkflowStatus.RUNNING if instance.status != WorkflowStatus.REPLAYING else WorkflowStatus.REPLAYING
            instance.started_at = instance.started_at or datetime.now(timezone.utc)
            
            # Hardening: Capture Trace ID for audit & continuity
            tid = correlation_id()
            if tid != "no-otel" and tid != "no-span":
                instance.metadata["original_trace_id"] = tid.split(":")[0]

            await self.persistence.save_instance(instance)
            await self.persistence.save_event(instance.id, "workflow_started", payload={"type": instance.workflow_type, "trace_id": tid})

            if _WS_AVAILABLE:
                from datetime import timezone
                await ws_manager.broadcast({
                    "type": "WORKFLOW_STARTED",
                    "project_id": instance.id,
                    "status": instance.status.value,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            try:
                while instance.status in (WorkflowStatus.RUNNING, WorkflowStatus.REPLAYING):
                    # Reload instance at loop start to catch external cancellation or status changes
                    loaded = await self.persistence.load_instance(instance.id)
                    if not loaded:
                        logger.error(f"Workflow {instance.id} disappeared during execution.")
                        break
                    instance = loaded

                    if instance.status == WorkflowStatus.CANCELLED:
                        logger.warning(f"[Workflow {instance.id}] Cancellation signal detected. Terminating loop.")
                        break

                    completed_ids = {
                        s.id for s in instance.steps
                        if s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
                    }

                    ready_steps = [
                        s for s in instance.steps
                        if s.status in (StepStatus.PENDING, StepStatus.REPLAY_PENDING)
                        and all(dep_id in completed_ids for dep_id in s.dependencies)
                    ]

                    # Condition Filter (Phase 28)
                    final_ready = []
                    for s in ready_steps:
                        if _condition_matches(s.condition, instance.context):
                            final_ready.append(s)
                        else:
                            logger.info(f"[Workflow {instance.id}] Skipping step {s.name} due to condition: {s.condition}")
                            s.status = StepStatus.SKIPPED
                            await self.persistence.save_step(instance.id, s)

                    ready_steps = final_ready

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
                            # Capture summary error from the first failed step found
                            failed_step = next((s for s in instance.steps if s.status == StepStatus.FAILED), None)
                            if failed_step:
                                instance.error = f"Step '{failed_step.name}' failed: {failed_step.error}"
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
                    add_span_event("workflow.batch_start", attributes={"steps": str(step_names)})

                    await asyncio.gather(
                        *[self._execute_step(instance, step) for step in ready_steps]
                    )

                    # Update persistence with the latest state after batch execution
                    await self.persistence.save_instance(instance)
                    if instance.status == WorkflowStatus.CANCELLED:
                        logger.warning(f"Workflow {instance.id} CANCELLED by signal.")
                        await self.persistence.save_event(instance.id, "workflow_cancelled")
                        return

                    await self.persistence.save_instance(instance)

                    if instance.status == WorkflowStatus.FAILED:
                        # Capture summary error if not already set
                        if not instance.error:
                            failed_step = next((s for s in instance.steps if s.status == StepStatus.FAILED), None)
                            if failed_step:
                                instance.error = f"Step '{failed_step.name}' failed: {failed_step.error}"
                        
                        await self.persistence.save_instance(instance)
                        await self.persistence.save_event(instance.id, "workflow_failed")
                        break

                from datetime import timezone
                instance.completed_at = datetime.now(timezone.utc)
                await self.persistence.save_instance(instance)
                terminal_event = "workflow_completed" if instance.status == WorkflowStatus.COMPLETED else "workflow_failed"
                await self.persistence.save_event(instance.id, terminal_event)

                if _WS_AVAILABLE:
                    await ws_manager.broadcast({
                        "type": "WORKFLOW_COMPLETED",
                        "project_id": instance.id,
                        "status": instance.status.value,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

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
                instance.error = str(e)
                try:
                    await self.persistence.save_instance(instance)
                except Exception:
                    pass
                raise

        # Wrap entire workflow in an OTel span
        with _otel_span("workflow.execute", attributes=span_attrs):
            await _run()

    async def suggest_fix(self, instance: WorkflowInstance, step_id: str) -> Dict[str, Any]:
        """
        [Phase 4: Metacognition] Analiz failed steps and suggest a fix (input override).
        """
        step = next((s for s in instance.steps if s.id == step_id), None)
        if not step or step.status != StepStatus.FAILED:
            return {"suggestion": "No diagnosis needed for active or successful steps."}

        logger.info(f"[Metacognition] Diagnosing failure in step {step.name}...")
        
        # In a real system, we call ModelOrchestrator here.
        # We simulate a smart suggestion based on common failure clusters.
        error_msg = step.error or "Unknown error"
        
        suggestion = {
            "reasoning": f"Analyzed error: '{error_msg}'. This appears to be a transient API failure or schema mismatch.",
            "recommended_override": {}
        }

        if "timeout" in error_msg.lower():
            suggestion["recommended_override"] = {"input": {**step.input_data, "timeout": 60}}
            suggestion["reasoning"] += " Recommendation: Increased timeout to 60s."
        elif "authentication" in error_msg.lower():
            suggestion["reasoning"] += " Recommendation: Check API key validity in context."
        
        return suggestion

    async def _execute_step(self, instance: WorkflowInstance, step: WorkflowStep):
        """Execute a single step with retry, wrapped in its own OTel child span."""
        step_attrs = {
            "step.id":           str(step.id),
            "step.name":         step.name,
            "step.action":       step.action,
            "step.max_retries":  step.max_retries,
            "workflow.id":       instance.id,
        }

        async def _run_step():
            # Check history to prevent redundant execution (DURABILITY)
            history = await self.persistence.load_history(instance.id)
            if any(e["event_type"] == "step_completed" and e["step_id"] == step.id for e in history):
                logger.info(f"[Step {step.name}] Already completed in history. Skipping.")
                step.status = StepStatus.COMPLETED
                return

            # ── Phase 14: Governance & Budget Check ────────────────────
            # 1. Global Budget Check
            current_total_cost = instance.context.get("_total_cost", 0.0)
            budget_check = cost_guard.check_budget_limit(current_total_cost)
            if budget_check["blocked"]:
                logger.error(f"[Budget] {budget_check['reason']}")
                step.status = StepStatus.FAILED
                step.error = budget_check["reason"]
                await self.persistence.save_step(instance.id, step)
                await self.persistence.save_event(instance.id, "budget_limit_breached", payload=budget_check)
                return

            # 2. Autonomy & Approval Check
            autonomy_check = autonomy_engine.check_execution_permission({
                "step_id": step.id,
                "step_name": step.name,
                "tool_name": step.action,
                "risk_score": step.input_data.get("_risk_score", 0.0)
            })

            if autonomy_check["requires_approval"]:
                logger.warning(f"[Autonomy] Approval required: {autonomy_check['reason']}")
                step.status = StepStatus.WAITING
                instance.status = WorkflowStatus.WAITING_APPROVAL
                
                await self.persistence.save_event(
                    instance.id, 
                    "step_waiting_approval", 
                    step_id=step.id,
                    payload={
                        "reason": autonomy_check["reason"],
                        "autonomy_level": autonomy_engine.config.get("current_global_level"),
                        "input_preview": step.input_data
                    }
                )
                
                await self.persistence.save_step(instance.id, step)
                await self.persistence.save_instance(instance)
                return

            # Approval Gate Logic (Legacy/Phase 2 fallback)
            if step.require_approval:
                # We check if the parent project has review_required=False (meaning it was approved)
                # This matches the existing Project.review_required column in core_models.py
                instance_reloaded = await self.persistence.load_instance(instance.id)
                project_needs_review = getattr(instance_reloaded, "review_required", False) 
                # Note: persistence.load_instance currently loads into WorkflowInstance which might not have all fields.
                # However, our engine loop reloads from persistence.

                if project_needs_review:
                    logger.info(f"[Step {step.name}] WAITING FOR APPROVAL.")
                    step.status = StepStatus.WAITING
                    instance.status = WorkflowStatus.WAITING_APPROVAL
                    await self.persistence.save_step(instance.id, step)
                    await self.persistence.save_instance(instance)
                    await self.persistence.save_event(instance.id, "step_waiting_approval", step_id=step.id)
                    return # Pause this step (and since it's gathered, it stops the batch)

            from datetime import timezone
            logger.info(f"[Step {step.name}] Starting action: {step.action}")
            step.status = StepStatus.RUNNING
            step.started_at = datetime.now(timezone.utc)
            await self.persistence.save_step(instance.id, step)
            await self.persistence.save_event(instance.id, "step_started", step_id=step.id)

            if _WS_AVAILABLE:
                await ws_manager.broadcast({
                    "type": "STEP_STARTED",
                    "project_id": instance.id,
                    "step_id": step.id,
                    "step_name": step.name,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            try:
                # Pre-execution Cancellation Check
                instance_check = await self.persistence.load_instance(instance.id)
                if instance_check and instance_check.status == WorkflowStatus.CANCELLED:
                    logger.warning(f"[Step {step.name}] Workflow cancelled before execution. Aborting.")
                    step.status = StepStatus.FAILED
                    return

                action_func = self._registry.get(step.action)
                if not action_func:
                    raise ValueError(f"Action '{step.action}' not registered in WorkflowEngine")

                # Actual execution wrapped in a potential cancellation listener
                result = await action_func(instance.context, **step.input_data)

                from datetime import timezone
                step.output_data = result if isinstance(result, dict) else {"result": result}
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                await self.persistence.save_event(instance.id, "step_completed", step_id=step.id, payload=step.output_data)

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
                add_span_event("step.error", attributes={"error": str(e), "attempt": step.retries + 1})

                if step.retries < step.max_retries:
                    step.retries += 1
                    step.status = StepStatus.PENDING
                    logger.info(f"[Step {step.name}] Scheduled for retry #{step.retries}")
                else:
                    step.status = StepStatus.FAILED
                    instance.status = WorkflowStatus.FAILED
                    instance.error = f"Step '{step.name}' failed after {step.max_retries} retries: {str(e)}"
                    set_span_attrs(**{"step.status": "failed", "step.error": str(e)})
                    await self.persistence.save_event(instance.id, "step_failed", step_id=step.id, payload={"error": str(e)})
                    logger.error(f"[Step {step.name}] Max retries exceeded. Workflow FAILED.")

            await self.persistence.save_step(instance.id, step)

            if _WS_AVAILABLE:
                from datetime import timezone
                await ws_manager.broadcast({
                    "type": "STEP_COMPLETED" if step.status == StepStatus.COMPLETED else "STEP_FAILED",
                    "project_id": instance.id,
                    "step_id": step.id,
                    "status": step.status.value,
                    "error": step.error,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        with _otel_span(f"step.{step.action}", attributes=step_attrs):
            await _run_step()


    # ── Replay Operations (Phase 2.1) ──────────────────────────────────────────

    async def replay(self, instance: WorkflowInstance, from_step_id: str, mode: str = "same_input", overrides: Optional[dict] = None, operator_id: str = "system", reason: str = "manual trigger"):
        """
        Force a workflow to re-execute from a specific point with full audit trail.
        - mode 'same_input': only reset the target step.
        - mode 'from_step': reset the target step and ALL downstream steps.
        - overrides: update the context or step input before replaying.
        """
        logger.info(f"[Replay] Triggered by {operator_id} for workflow {instance.id} from step {from_step_id} (Mode: {mode}). Reason: {reason}")
        
        target_found = False
        steps_to_reset = [from_step_id]

        if mode == "from_step":
            # Collect all downstream dependents recursively (Dependency Graph Reset)
            def collect_downstream(step_id):
                for s in instance.steps:
                    if step_id in s.dependencies and s.id not in steps_to_reset:
                        steps_to_reset.append(s.id)
                        collect_downstream(s.id)
            collect_downstream(from_step_id)

        # Reset phase with COMPENSATION support
        for s in instance.steps:
            if s.id in steps_to_reset:
                # If step was COMPLETED, we must check for compensation
                if s.status == StepStatus.COMPLETED and s.compensation_action:
                    logger.warning(f"[Compensation] Undoing step {s.name} ({s.id}) via {s.compensation_action}")
                    # In a real system, we would await self._registry[s.compensation_action](s.input_data, s.output_data)
                    # For now, we log the audit event
                    await self.persistence.save_event(instance.id, "step_compensated", step_id=s.id, payload={
                        "action": s.compensation_action,
                        "operator_id": operator_id,
                        "original_result": s.output_data
                    })
                    s.is_compensated = True

                s.status = StepStatus.REPLAY_PENDING if s.id == from_step_id else StepStatus.PENDING
                s.completed_at = None
                s.started_at = None
                s.error = None
                if s.id == from_step_id and overrides:
                    # Deeper Hardening: Validate override keys AND types against schema
                    if "input" in overrides:
                        input_to_check = overrides["input"]
                        for key, value in input_to_check.items():
                            if key not in s.input_data:
                                logger.warning(f"[Replay] Unknown key: {key} (Step: {s.name})")
                            
                            # Type Validation if schema exists
                            if s.input_schema and key in s.input_schema:
                                expected_type = s.input_schema[key].get("type")
                                actual_val = value
                                
                                # Robust validation for basic types
                                type_map = {
                                    "integer": int,
                                    "string": str,
                                    "boolean": bool,
                                    "number": (int, float),
                                    "array": list,
                                    "object": dict
                                }
                                
                                expected_py_type = type_map.get(expected_type)
                                if expected_py_type and not isinstance(actual_val, expected_py_type):
                                    raise ValueError(
                                        f"Validation Error in step '{s.name}': "
                                        f"Field '{key}' expected type '{expected_type}', "
                                        f"but got '{type(actual_val).__name__}'."
                                    )
                    
                    # Apply overrides to step input
                    s.input_data.update(overrides.get("input", {}))
                target_found = True

        if not target_found:
            raise ValueError(f"Step {from_step_id} not found in workflow {instance.id}")

        if overrides and "context" in overrides:
            # Apply global context updates
            instance.context.update(overrides["context"])

        instance.status = WorkflowStatus.REPLAYING
        await self.persistence.save_instance(instance)
        
        # Comprehensive audit log entry
        original_tid = instance.metadata.get("original_trace_id", "unknown")
        await self.persistence.save_event(
            instance.id, 
            "workflow_replay_started", 
            operator_id=operator_id,
            payload={
                "from_step": from_step_id, 
                "mode": mode,
                "reason": reason,
                "reset_steps": steps_to_reset,
                "has_overrides": overrides is not None,
                "original_trace_id": original_tid,
                "correlation_trace_id": correlation_id().split(":")[0]
            }
        )
        
        # Start execution loop
        await self.execute(instance)
