import pytest
from pathlib import Path
from services.project_factory.policy_evidence_bundle import build_policy_evidence_bundle
import json

def test_build_policy_evidence_bundle_creates_files(tmp_path):
    # Setup mock workspace
    workspace = tmp_path
    
    autopilot_dir = workspace / "project_outputs" / "project_factory" / "policy_autopilot"
    autopilot_dir.mkdir(parents=True)
    
    # Create some mock artifacts
    (autopilot_dir / "policy_proposals.json").write_text('{"mock": true}')
    (autopilot_dir / "policy_pr_creation.json").write_text('{"mock": true}')
    
    gov_pack = autopilot_dir / "policy_governance_evidence_pack"
    gov_pack.mkdir()
    (gov_pack / "policy_governance_manifest.json").write_text('{"mock": true}')
    
    archive_dir = autopilot_dir / "policy_release_archive"
    archive_dir.mkdir()
    
    count = build_policy_evidence_bundle(archive_dir, str(workspace))
    
    assert count == 3
    assert (archive_dir / "policy_evidence_bundle" / "policy_proposals.json").exists()
    assert (archive_dir / "policy_evidence_bundle" / "policy_pr_creation.json").exists()
    assert (archive_dir / "policy_evidence_bundle" / "policy_governance_manifest.json").exists()
