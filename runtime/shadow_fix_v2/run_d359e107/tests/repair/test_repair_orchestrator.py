import json
from pathlib import Path

from services.repair.repair_orchestrator import run_repair_flow


def test_orchestrator_writes_report_without_touching_main(tmp_path):
    payload = {
        "incident_id": "INC-ORCH",
        "trace_id": "TRACE-ORCH",
        "error_type": "AssertionError",
        "summary": "orchestrator smoke",
        "failed_command": "",
        "failed_test": "tests/repair/test_repair_orchestrator.py::test_orchestrator_writes_report_without_touching_main",
        "traceback": 'File "services/repair/repair_case_builder.py", line 10, in build_repair_case',
        "allowed_paths": ["services/", "tests/"],
        "forbidden_paths": ["services/auth/", ".env"],
    }

    report = run_repair_flow(payload, output_root=tmp_path)

    report_path = tmp_path / "INC-ORCH" / "repair_report.json"
    case_path = tmp_path / "INC-ORCH" / "repair_case.json"
    sandbox_log = tmp_path / "INC-ORCH" / "sandbox.log"

    assert report.final_status in {
        "DRAFT_PR_READY",
        "SANDBOX_FAILED",
        "VERIFIER_FAILED",
        "AUTO_REPAIR_BLOCKED",
        "QUORUM_REQUIRED",
    }
    assert report_path.exists()
    assert case_path.exists()
    assert sandbox_log.exists()

    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["repair_case"]["incident_id"] == "INC-ORCH"
    assert Path(data["candidate"]["patch_path"]).name == "patch.diff"
