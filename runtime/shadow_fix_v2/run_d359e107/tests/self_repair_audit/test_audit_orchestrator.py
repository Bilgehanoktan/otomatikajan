import os
import json
import pytest
from services.self_repair_audit.audit_orchestrator import AuditOrchestrator

def test_orchestrator_execution(tmp_path):
    workspace = str(tmp_path)
    
    # Bootstrap minimum directory structures so scanners can execute without crashing
    os.makedirs(os.path.join(workspace, "apps", "refine_control_plane", "src", "app"), exist_ok=True)
    os.makedirs(os.path.join(workspace, "services", "workflow_api"), exist_ok=True)
    os.makedirs(os.path.join(workspace, "configs"), exist_ok=True)
    os.makedirs(os.path.join(workspace, "workflows"), exist_ok=True)

    # Let's verify read-only behavior by making a snapshot of the workspace before running
    def get_dir_snapshot(dir_path):
        snapshot = {}
        for root, _, files in os.walk(dir_path):
            # Ignore project_outputs folder which is where output artifacts should be written
            if "project_outputs" in root:
                continue
            for file in files:
                full_p = os.path.join(root, file)
                snapshot[full_p] = os.path.getmtime(full_p)
        return snapshot

    initial_snapshot = get_dir_snapshot(workspace)

    # Initialize Orchestrator and run
    orch = AuditOrchestrator(workspace)
    report = orch.execute_full_audit()

    # 1. Assert run output files were created properly in the target path
    run_id = report["audit_run_id"]
    output_dir = os.path.join(workspace, "project_outputs", "audit_runs", run_id)
    assert os.path.exists(output_dir)
    assert os.path.isdir(output_dir)

    expected_artifacts = [
        "system_context.json",
        "api_contract_audit.json",
        "dashboard_health_audit.json",
        "test_build_audit.json",
        "security_guardrail_audit.json",
        "project_factory_audit.json",
        "classified_findings.json",
        "audit_report.json"
    ]
    # Let's dynamically check if they were written
    written_files = os.listdir(output_dir)
    for expected in expected_artifacts:
        assert expected in written_files, f"Expected artifact '{expected}' was not found in written files: {written_files}"


    # 2. Check report content structure
    assert report["scanner"] == "create_audit_report"
    assert "summary" in report
    assert "total_findings" in report["summary"]
    
    # 3. VERIFY READ-ONLY (No files outside project_outputs were changed or added)
    final_snapshot = get_dir_snapshot(workspace)
    # Check that every file in the final snapshot existed in the initial snapshot and was not modified
    for path, mtime in final_snapshot.items():
        assert path in initial_snapshot, f"File {path} was newly created outside project_outputs folder!"
        assert initial_snapshot[path] == mtime, f"File {path} was modified during the audit run!"
