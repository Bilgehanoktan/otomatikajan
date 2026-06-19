"""Tests for Release Archiver."""
import pytest
from services.project_factory.release_archiver import build_release_archive


def test_build_release_archive(monkeypatch, tmp_path):
    """build_release_archive orchestrates bundle and report creation."""
    
    monkeypatch.setattr("services.project_factory.release_archiver.build_evidence_bundle", lambda p, r: (["file1"], ["file2"]))
    
    closure_report_called = False
    def mock_generate_closure_report(**kwargs):
        nonlocal closure_report_called
        closure_report_called = True
        
    monkeypatch.setattr("services.project_factory.release_archiver.generate_closure_report", mock_generate_closure_report)
    monkeypatch.setattr("services.project_factory.release_archiver.write_release_manifest", lambda p, d, r: None)
    
    # Create dummy final_operator_decision to test copy
    project_dir = tmp_path / "project_outputs" / "project_factory" / "PF-1"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "final_operator_decision.json").write_text("{}")
    
    manifest = build_release_archive(
        project_id="PF-1",
        release_id="REL-1",
        operator_id="op1",
        rationale="test",
        workspace_root=str(tmp_path)
    )
    
    assert closure_report_called
    assert manifest.project_id == "PF-1"
    assert manifest.release_id == "REL-1"
    assert manifest.status == "RELEASE_ARCHIVE_READY"
    assert manifest.evidence_count == 1
    assert manifest.production_apply_performed is False
    assert manifest.merge_performed is False
    assert manifest.deploy_performed is False
    
    # Check that final_operator_decision was copied
    assert (project_dir / "release_archive" / "final_operator_decision.json").exists()
