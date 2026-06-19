import pytest
import os
import json
from services.project_factory.policy_release_archiver import create_policy_release_archive

def test_create_policy_release_archive(tmp_path):
    workspace = tmp_path
    autopilot_dir = workspace / "project_outputs" / "project_factory" / "policy_autopilot"
    autopilot_dir.mkdir(parents=True)
    
    # Create mock artifacts
    (autopilot_dir / "policy_proposals.json").write_text('{"mock": true}')
    
    manifest = create_policy_release_archive("POL-PF-001", "operator_1", "FINAL_POLICY_APPROVED", str(workspace))
    
    assert manifest.release_id == "PREL-POL-PF-001"
    assert manifest.final_decision == "FINAL_POLICY_APPROVED"
    assert manifest.production_apply_performed is False
    assert manifest.policy_files_modified is False
    assert manifest.learning_memory_synced is True
    
    archive_dir = autopilot_dir / "policy_release_archive"
    assert (archive_dir / "policy_release_manifest.json").exists()
    assert (archive_dir / "policy_closure_report.md").exists()
    assert (archive_dir / "policy_learning_memory_sync.json").exists()
    assert (archive_dir / "policy_evidence_bundle" / "policy_proposals.json").exists()
