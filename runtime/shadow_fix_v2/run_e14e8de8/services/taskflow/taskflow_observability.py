from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StepMetric:
    workflow_id: str
    step_id: str
    incident_id: str
    trace_id: str
    duration_seconds: float = 0.0
    risk_score: float = 0.0
    changed_file_count: int = 0
    sandbox_exit_code: int | None = None
    verifier_status: str | None = None
    cost_usd: float = 0.0


def build_step_metric(
    *,
    workflow_id: str,
    step_id: str,
    incident_id: str,
    trace_id: str,
    context: dict,
    duration_seconds: float,
) -> StepMetric:
    candidate = context.get("repair_candidate")
    sandbox = context.get("sandbox_result")
    verifier = context.get("verifier_result") or {}
    return StepMetric(
        workflow_id=workflow_id,
        step_id=step_id,
        incident_id=incident_id,
        trace_id=trace_id,
        duration_seconds=round(duration_seconds, 4),
        risk_score=float(context.get("risk_score") or 0.0),
        changed_file_count=len(getattr(candidate, "changed_files", []) or []),
        sandbox_exit_code=getattr(sandbox, "exit_code", None),
        verifier_status=verifier.get("status") if isinstance(verifier, dict) else None,
        cost_usd=float(context.get("cost_usd") or 0.0),
    )

