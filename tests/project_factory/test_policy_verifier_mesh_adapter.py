import pytest
import os
import json
import tempfile
from services.project_factory.policy_verifier_mesh_adapter import run_policy_verifier_mesh
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

@pytest.fixture
def workspace_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        p_dir = _resolve_policy_autopilot_dir(temp_dir)
        p_dir.mkdir(parents=True, exist_ok=True)
        yield temp_dir

def test_verifier_mesh_success(workspace_dir):
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    
    with open(p_dir / "policy_pr_creation.json", "w", encoding="utf-8") as f:
        json.dump({
            "merge_performed": False,
            "force_push_performed": False,
            "production_direct_write": False,
            "is_draft": True,
            "branch_name": "codex/policy-update",
            "modified_files": ["agents/policy.json"]
        }, f)
        
    with open(p_dir / "policy_apply_preview.json", "w", encoding="utf-8") as f:
        json.dump({
            "production_apply_performed": False
        }, f)
        
    with open(p_dir / "policy_draft_pr_plan.json", "w", encoding="utf-8") as f:
        json.dump({
            "git_operations_performed": False,
            "files_to_apply": ["agents/policy.json"]
        }, f)
        
    # Write a dummy governance manifest in the right directory
    pack_dir = p_dir / "policy_governance_evidence_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    with open(pack_dir / "policy_governance_manifest.json", "w", encoding="utf-8") as f:
        json.dump({
            "git_operations_performed": False
        }, f)
        
    report = run_policy_verifier_mesh("POL-1", workspace_dir)
    
    assert report.status == "PASSED"
    assert all(c.status == "PASSED" for c in report.checks)

def test_verifier_mesh_failed_merge(workspace_dir):
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    
    with open(p_dir / "policy_pr_creation.json", "w", encoding="utf-8") as f:
        json.dump({
            "merge_performed": True, # This should fail it
            "force_push_performed": False,
            "production_direct_write": False,
            "is_draft": True,
            "branch_name": "codex/policy-update",
            "modified_files": ["agents/policy.json"]
        }, f)
        
    with open(p_dir / "policy_apply_preview.json", "w", encoding="utf-8") as f:
        json.dump({"production_apply_performed": False}, f)
        
    with open(p_dir / "policy_draft_pr_plan.json", "w", encoding="utf-8") as f:
        json.dump({"git_operations_performed": False, "files_to_apply": ["agents/policy.json"]}, f)
        
    report = run_policy_verifier_mesh("POL-1", workspace_dir)
    
    assert report.status == "FAILED"
    failed_checks = [c.name for c in report.checks if c.status == "FAILED"]
    assert "pr_creation_merge_performed" in failed_checks

def test_verifier_mesh_failed_forbidden_file(workspace_dir):
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    
    with open(p_dir / "policy_pr_creation.json", "w", encoding="utf-8") as f:
        json.dump({
            "merge_performed": False,
            "force_push_performed": False,
            "production_direct_write": False,
            "is_draft": True,
            "branch_name": "codex/policy-update",
            "modified_files": ["agents/.env.local"] # Forbidden keyword!
        }, f)
        
    with open(p_dir / "policy_apply_preview.json", "w", encoding="utf-8") as f:
        json.dump({"production_apply_performed": False}, f)
        
    with open(p_dir / "policy_draft_pr_plan.json", "w", encoding="utf-8") as f:
        json.dump({"git_operations_performed": False, "files_to_apply": ["agents/.env.local"]}, f)
        
    report = run_policy_verifier_mesh("POL-1", workspace_dir)
    
    assert report.status == "FAILED"
    failed_checks = [c.name for c in report.checks if c.status == "FAILED"]
    assert "modified_files_scope" in failed_checks
