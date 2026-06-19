from pathlib import Path

from services.taskflow.taskflow_artifacts import write_json_artifact
from services.taskflow.taskflow_models import GateDecision, TaskStep, WorkflowRun


def test_workflow_run_and_step_models_are_created():
    step = TaskStep(step_id="build_repair_case", step_type="deterministic", handler="x.y")
    run = WorkflowRun(
        workflow_id="self_repair_v1",
        workflow_name="Self Repair",
        incident_id="INC-MODEL",
        trace_id="TRACE-MODEL",
        steps=[step],
    )
    gate = GateDecision(gate_id="approval_gate", decision="DRAFT_PR_ALLOWED", risk_score=0.2, reason="low")

    assert run.workflow_id == "self_repair_v1"
    assert run.steps[0].status == "PENDING"
    assert gate.decision == "DRAFT_PR_ALLOWED"


def test_task_artifact_sha256_is_recorded(tmp_path):
    artifact = write_json_artifact(
        "INC-ART",
        "build_repair_case",
        "repair_case.json",
        {"incident_id": "INC-ART"},
        output_root=tmp_path,
    )

    assert Path(artifact.path).exists()
    assert len(artifact.sha256) == 64

