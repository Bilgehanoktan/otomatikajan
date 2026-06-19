from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any, Callable

import yaml

from services.taskflow.taskflow_artifacts import artifact_for_existing_file, write_json_artifact
from services.taskflow.taskflow_events import (
    GATE_WAITING,
    STEP_BLOCKED,
    STEP_FAILED,
    STEP_STARTED,
    STEP_SUCCEEDED,
    WORKFLOW_COMPLETED,
    WORKFLOW_STARTED,
    create_event,
)
from services.taskflow.taskflow_models import TaskStep, WorkflowRun, to_plain_data, utc_now_iso
from services.taskflow.taskflow_observability import build_step_metric
from services.taskflow.taskflow_retries import attempts_allowed, should_retry
from services.taskflow.taskflow_state_machine import transition_step


def _workflow_path(workflow_name: str) -> Path:
    candidate = Path(workflow_name)
    if candidate.exists():
        return candidate
    name = workflow_name if workflow_name.endswith(".yaml") else f"{workflow_name}.yaml"
    return Path("workflows") / name


def load_workflow_contract(workflow_name: str) -> dict[str, Any]:
    path = _workflow_path(workflow_name)
    if not path.exists():
        raise FileNotFoundError(f"Workflow contract not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_handler(handler_path: str) -> Callable[[dict[str, Any]], dict[str, Any] | None]:
    module_name, function_name = handler_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    handler = getattr(module, function_name)
    return handler


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
    for operator in (">=", "<=", "==", ">", "<"):
        if operator in condition:
            left_raw, right_raw = condition.split(operator, 1)
            left = _condition_value(left_raw, context)
            right = _condition_value(right_raw, context)
            if operator == "==":
                return left == right
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
    raise ValueError(f"Unsupported workflow condition: {condition}")


def _build_steps(contract: dict[str, Any]) -> list[TaskStep]:
    steps = []
    for item in contract.get("steps", []):
        steps.append(
            TaskStep(
                step_id=str(item["id"]),
                step_type=str(item.get("type") or "deterministic"),
                handler=str(item["handler"]),
                retry=int(item.get("retry") or 0),
                timeout_seconds=item.get("timeout_seconds"),
                condition=item.get("condition"),
                always_run=bool(item.get("always_run", False)),
                artifact=item.get("artifact"),
            )
        )
    return steps


def run_workflow(
    workflow_name: str,
    input_payload: dict[str, Any],
    *,
    output_root: str | Path | None = None,
) -> WorkflowRun:
    contract = load_workflow_contract(workflow_name)
    incident_id = str(input_payload.get("incident_id") or input_payload.get("id") or "INC-UNKNOWN")
    trace_id = str(input_payload.get("trace_id") or "")
    workflow_id = str(contract.get("workflow_id") or workflow_name)
    run = WorkflowRun(
        workflow_id=workflow_id,
        workflow_name=str(contract.get("name") or workflow_name),
        incident_id=incident_id,
        trace_id=trace_id,
        steps=_build_steps(contract),
    )
    context: dict[str, Any] = {
        "input_payload": input_payload,
        "incident_id": incident_id,
        "trace_id": trace_id,
        "workflow_id": workflow_id,
        "run_id": run.run_id,
        "output_root": str(output_root) if output_root is not None else None,
    }
    metrics = []
    run.status = "RUNNING"
    run.events.append(create_event(WORKFLOW_STARTED, workflow_id=workflow_id, incident_id=incident_id, trace_id=trace_id))

    for step in run.steps:
        run.current_step = step.step_id
        if run.status == "FAILED" and not step.always_run:
            step.status = transition_step(step.status, "SKIPPED")
            continue
        if not step.always_run and not _condition_matches(step.condition, context):
            step.status = transition_step(step.status, "SKIPPED")
            continue

        step.status = transition_step(step.status, "READY")
        max_attempts = attempts_allowed(step.retry)
        while step.attempts < max_attempts:
            step.attempts += 1
            started = time.monotonic()
            step.started_at = utc_now_iso()
            step.status = transition_step(step.status, "RUNNING")
            run.events.append(
                create_event(
                    STEP_STARTED,
                    workflow_id=workflow_id,
                    step_id=step.step_id,
                    incident_id=incident_id,
                    trace_id=trace_id,
                )
            )
            try:
                result = _load_handler(step.handler)(context) or {}
                elapsed = time.monotonic() - started
                if step.timeout_seconds is not None and elapsed > float(step.timeout_seconds):
                    raise TimeoutError(f"Step {step.step_id} exceeded timeout_seconds={step.timeout_seconds}")
                context.update(result)

                # Validate step artifact contract
                if step.artifact:
                    from services.repair.taskflow_artifacts import artifact_dir_for_run
                    expected_dir = artifact_dir_for_run(incident_id, run.run_id, output_root)
                    expected_path = expected_dir / step.artifact
                    if not expected_path.exists():
                        raise ValueError(f"Required artifact '{step.artifact}' missing for step '{step.step_id}'")

                step.status = transition_step(step.status, "SUCCEEDED")
                step.finished_at = utc_now_iso()
                run.events.append(
                    create_event(
                        STEP_SUCCEEDED,
                        workflow_id=workflow_id,
                        step_id=step.step_id,
                        incident_id=incident_id,
                        trace_id=trace_id,
                    )
                )
                if result.get("artifact_path"):
                    artifact = artifact_for_existing_file(step.step_id, result["artifact_path"], str(result.get("artifact_type") or "json"))
                    step.artifacts.append(artifact)
                    run.artifacts.append(artifact)
                metrics.append(
                    build_step_metric(
                        workflow_id=workflow_id,
                        step_id=step.step_id,
                        incident_id=incident_id,
                        trace_id=trace_id,
                        context=context,
                        duration_seconds=elapsed,
                    )
                )
                if result.get("workflow_status") == "WAITING_HUMAN":
                    run.events.append(
                        create_event(GATE_WAITING, workflow_id=workflow_id, step_id=step.step_id, incident_id=incident_id, trace_id=trace_id)
                    )
                if result.get("workflow_status") == "BLOCKED":
                    run.events.append(
                        create_event(STEP_BLOCKED, workflow_id=workflow_id, step_id=step.step_id, incident_id=incident_id, trace_id=trace_id)
                    )
                break
            except Exception as exc:
                step.error = str(exc)
                step.finished_at = utc_now_iso()
                step.status = transition_step(step.status, "FAILED")
                run.events.append(
                    create_event(
                        STEP_FAILED,
                        workflow_id=workflow_id,
                        step_id=step.step_id,
                        incident_id=incident_id,
                        trace_id=trace_id,
                        payload={"error": str(exc)},
                    )
                )
                if should_retry(step.attempts, step.retry):
                    step.status = transition_step(step.status, "RETRYING")
                    step.status = transition_step(step.status, "READY")
                    continue
                step.status = transition_step(step.status, "BLOCKED")
                run.status = "FAILED"
                run.final_decision = "REPAIR_FAILED"
                break

    run.risk_score = float(context.get("risk_score") or 0.0)
    run.final_decision = str(context.get("final_decision") or context.get("risk_decision_status") or run.final_decision or "")
    if run.status != "FAILED":
        workflow_status = context.get("workflow_status")
        if workflow_status in {"WAITING_HUMAN", "BLOCKED", "DRAFT_PR_READY"}:
            run.status = str(workflow_status)
        elif run.final_decision in {"DRAFT_PR_READY", "DRAFT_PR_ALLOWED"}:
            run.status = "DRAFT_PR_READY"
        else:
            run.status = "COMPLETED"
    run.finished_at = utc_now_iso()
    run.events.append(create_event(WORKFLOW_COMPLETED, workflow_id=workflow_id, incident_id=incident_id, trace_id=trace_id))
    trace_payload = {"workflow_run": to_plain_data(run), "metrics": to_plain_data(metrics)}
    artifact = write_json_artifact(incident_id, "taskflow_trace", "taskflow_trace.json", trace_payload, output_root=output_root)
    run.artifacts.append(artifact)

    # Build and write the artifact manifest for Phase 4 auditability
    from services.repair.taskflow_artifacts import build_artifact_manifest, artifact_dir_for_run, get_sha256
    from services.taskflow.taskflow_models import TaskArtifact
    manifest = build_artifact_manifest(incident_id, run.run_id, workflow_id, contract.get("steps", []), output_root=output_root)
    manifest_file = artifact_dir_for_run(incident_id, run.run_id, output_root) / "artifact_manifest.json"
    try:
        manifest_path_str = str(manifest_file.relative_to(Path.cwd()))
    except ValueError:
        manifest_path_str = str(manifest_file)
    manifest_artifact = TaskArtifact(
        artifact_id="taskflow:artifact_manifest",
        step_id="taskflow",
        path=manifest_path_str,
        artifact_type="json",
        sha256=get_sha256(manifest_file),
    )
    run.artifacts.append(manifest_artifact)

    return run
