from services.taskflow.taskflow_engine import load_workflow_contract, run_workflow


def test_self_repair_workflow_contract_loads_steps():
    contract = load_workflow_contract("self_repair_v1")

    assert contract["workflow_id"] == "self_repair_v1"
    assert [step["id"] for step in contract["steps"]][:3] == [
        "build_repair_case",
        "localize_code",
        "create_repair_plan",
    ]


def test_engine_runs_self_repair_workflow_and_writes_trace(tmp_path):
    payload = {
        "incident_id": "INC-TF",
        "trace_id": "TRACE-TF",
        "summary": "TaskFlow smoke",
        "failed_command": "",
        "failed_test": "tests/repair/test_x.py::test_y",
        "traceback": 'File "services/repair/repair_case_builder.py", line 10, in build_repair_case',
        "allowed_paths": ["services/", "tests/"],
        "forbidden_paths": ["services/auth/", ".env"],
    }

    run = run_workflow("self_repair_v1", payload, output_root=tmp_path)

    assert run.status in {"DRAFT_PR_READY", "WAITING_HUMAN", "BLOCKED", "COMPLETED"}
    assert (tmp_path / "INC-TF" / "repair_case.json").exists()
    assert (tmp_path / "INC-TF" / "repair_plan.json").exists()
    assert (tmp_path / "INC-TF" / "patch.diff").exists()
    assert (tmp_path / "INC-TF" / "sandbox.log").exists()
    assert (tmp_path / "INC-TF" / "repair_report.json").exists()
    assert (tmp_path / "INC-TF" / "taskflow_trace.json").exists()

