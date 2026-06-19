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

    print("GENERATED FILES:", [str(p.relative_to(tmp_path)) for p in tmp_path.glob("**/*") if p.is_file()])
    assert run.incident_id == "INC-E2E"
    
    # Faz 4/5/6: Verify artifact directory and specific run artifacts
    run_dir = tmp_path / "INC-E2E" / "taskflow" / run.run_id
    assert run_dir.exists()
    assert (run_dir / "failure_context.json").exists()
    assert (run_dir / "repair_case.json").exists()
    assert (run_dir / "repair_plan.json").exists()
    assert (run_dir / "patch_candidates.json").exists()
    assert (run_dir / "sandbox_result.json").exists()
    assert (run_dir / "verifier_mesh_result.json").exists()
    assert (run_dir / "human_gate_decision.json").exists()
    assert (run_dir / "pr_review.json").exists()
    assert (run_dir / "risk_report.json").exists()
    assert (tmp_path / "INC-E2E" / "patch.diff").exists()
    assert (tmp_path / "INC-E2E" / "taskflow_trace.json").exists()

