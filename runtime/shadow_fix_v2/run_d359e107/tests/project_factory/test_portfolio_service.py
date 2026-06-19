import os
import json
import pytest

from services.project_factory.models import ProjectFactoryIntake, RebuildArchiveRequest
from services.project_factory.portfolio_service import rebuild_portfolio
from services.project_factory.artifacts import _resolve_project_factory_root

def test_portfolio_service_orchestration(tmp_path):
    root = _resolve_project_factory_root(str(tmp_path))
    root.mkdir(parents=True, exist_ok=True)
    
    # Create a project
    p1 = root / "PF-ORCH"
    p1.mkdir()
    intake = ProjectFactoryIntake(
        project_id="PF-ORCH",
        source_suggestion_id="S-1",
        audit_run_id="A-1",
        title="Test Project",
        problem_statement="Prob",
        recommended_action="Fix",
        status="PROJECT_CLOSED"
    )
    (p1 / "project_brief.json").write_text(intake.model_dump_json())
    (p1 / "final_operator_decision.json").write_text(json.dumps({"decision": "FINAL_APPROVED"}))
    
    archive_dir = p1 / "release_archive"
    archive_dir.mkdir()
    (archive_dir / "release_manifest.json").write_text(json.dumps({"release_id": "REL-123"}))
    
    req = RebuildArchiveRequest(
        operator_id="ADMIN",
        rationale="Nightly build"
    )
    
    result = rebuild_portfolio(req, str(tmp_path))
    
    assert result["status"] == "success"
    assert result["archive_summary"]["total_projects"] == 1
    assert result["metrics_summary"]["release_archive_count"] == 1
    
    # Verify log was written
    log_file = root / "archive_index_logs.jsonl"
    assert log_file.exists()
    logs = log_file.read_text().splitlines()
    assert len(logs) == 1
    log_data = json.loads(logs[0])
    assert log_data["operator_id"] == "ADMIN"
    assert log_data["rationale"] == "Nightly build"
