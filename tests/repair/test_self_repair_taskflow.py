from services.taskflow.taskflow_engine import run_workflow


def test_sample_failed_test_payload_runs_end_to_end(tmp_path):
    payload = {
        "incident_id": "INC-E2E",
        "trace_id": "trace-demo-001",
        "error_type": "failed_test",
        "summary": "Workflow status mapping test failed.",
        "failed_command": "",
        "failed_test": "test_failed_status_maps_to_error",
        "traceback": "AssertionError at libs/workflow/models.py",
        "related_logs": ["API expected normalized status ERROR"],
        "allowed_paths": ["libs/workflow/", "services/workflow_api/", "tests/workflow/"],
        "forbidden_paths": [".env", "services/auth/", "libs/config.py"],
    }

    run = run_workflow("self_repair_v1", payload, output_root=tmp_path)

    assert run.incident_id == "INC-E2E"
    assert (tmp_path / "INC-E2E" / "repair_case.json").exists()
    assert (tmp_path / "INC-E2E" / "repair_plan.json").exists()
    assert (tmp_path / "INC-E2E" / "patch.diff").exists()
    assert (tmp_path / "INC-E2E" / "sandbox.log").exists()
    assert (tmp_path / "INC-E2E" / "repair_report.json").exists()
    assert (tmp_path / "INC-E2E" / "taskflow_trace.json").exists()

