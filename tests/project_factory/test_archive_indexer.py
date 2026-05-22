import os
import json
import pytest
from pathlib import Path

from services.project_factory.models import ProjectFactoryIntake
from services.project_factory.archive_indexer import rebuild_archive_index
from services.project_factory.artifacts import _resolve_project_factory_root

def test_archive_indexer(tmp_path):
    root = _resolve_project_factory_root(str(tmp_path))
    root.mkdir(parents=True, exist_ok=True)
    
    # Create a closed project
    p1 = root / "PF-CLOSED"
    p1.mkdir()
    intake1 = ProjectFactoryIntake(
        project_id="PF-CLOSED",
        source_suggestion_id="S-1",
        audit_run_id="A-1",
        title="Closed Project",
        problem_statement="Problem 1",
        recommended_action="Fix it",
        status="PROJECT_CLOSED"
    )
    (p1 / "project_brief.json").write_text(intake1.model_dump_json())
    (p1 / "final_operator_decision.json").write_text(json.dumps({"decision": "FINAL_APPROVED"}))
    
    # Create an active project
    p2 = root / "PF-ACTIVE"
    p2.mkdir()
    intake2 = ProjectFactoryIntake(
        project_id="PF-ACTIVE",
        source_suggestion_id="S-2",
        audit_run_id="A-2",
        title="Active Project",
        problem_statement="Problem 2",
        recommended_action="Fix it",
        status="HUMAN_GATE_WAITING"
    )
    (p2 / "project_brief.json").write_text(intake2.model_dump_json())
    (p2 / "candidate_review.json").write_text(json.dumps({"quality_score": 95, "risk_score": 10}))
    
    # Create an invalid project (no brief)
    p3 = root / "PF-INVALID"
    p3.mkdir()
    (p3 / "some_file.txt").write_text("hello")
    
    # Run indexer
    archive = rebuild_archive_index(str(tmp_path))
    
    assert archive.total_projects == 2
    assert archive.closed_projects == 1
    assert archive.active_projects == 1
    assert archive.blocked_projects == 0
    assert len(archive.projects) == 2
    
    p1_entry = next(p for p in archive.projects if p.project_id == "PF-CLOSED")
    assert p1_entry.status == "PROJECT_CLOSED"
    assert p1_entry.final_decision == "FINAL_APPROVED"
    
    p2_entry = next(p for p in archive.projects if p.project_id == "PF-ACTIVE")
    assert p2_entry.quality_score == 95
    assert p2_entry.risk_score == 10
    
    # Check that file was written
    idx_path = root / "archive_index.json"
    assert idx_path.exists()
