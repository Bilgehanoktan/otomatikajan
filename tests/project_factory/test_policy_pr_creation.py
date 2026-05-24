import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.project_factory.models import PolicyPRCreationRequest
from services.project_factory.policy_pr_creation_service import execute_policy_pr_creation
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

@pytest.fixture
def workspace_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .agents/policy_autopilot
        p_dir = _resolve_policy_autopilot_dir(temp_dir)
        p_dir.mkdir(parents=True, exist_ok=True)
        yield temp_dir

@patch("services.project_factory.policy_pr_creation_service.PolicyGitWorkspace")
@patch("services.project_factory.policy_pr_creation_service.PolicyGitHubPRAdapter")
def test_execute_policy_pr_creation_success(mock_gh_adapter, mock_git_workspace, workspace_dir):
    # Setup mocks
    mock_git_instance = mock_git_workspace.return_value
    mock_git_instance.commit.return_value = "mocksha123"
    
    mock_gh_instance = mock_gh_adapter.return_value
    mock_gh_instance.create_draft_pr.return_value = (True, "https://github.com/mock/pr/1", "")
    
    proposal_id = "POL-1234"
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    
    # Write prerequisites
    with open(p_dir / "policy_draft_pr_plan.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "branch_name": "codex/policy-123",
            "target_branch": "main",
            "draft_title": "Update policy",
            "files_to_apply": ["agents/policy.json"],
            "git_operations_performed": False
        }, f)
        
    with open(p_dir / "policy_apply_preview.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "production_apply_performed": False,
            "policy_files_modified": False,
            "blocking_risks": [],
            "preview_changes": [
                {"change_type": "APPEND", "target_file": "agents/policy.json"}
            ]
        }, f)
        
    pack_dir = p_dir / "policy_governance_evidence_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    with open(pack_dir / "policy_governance_manifest.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "ready_for_operator_pr_creation": True
        }, f)
        
    request = PolicyPRCreationRequest(
        operator_id="ADMIN",
        rationale="Approved",
        risk_acknowledgement=True,
        mode="safe_local_or_mock"
    )
    
    result = execute_policy_pr_creation(proposal_id, request, workspace_root=workspace_dir)
    
    assert result["status"] == "POLICY_DRAFT_PR_CREATED"
    assert result["branch_name"] == "codex/policy-123"
    assert result["commit_sha"] == "mocksha123"
    assert result["pr_url"] == "https://github.com/mock/pr/1"
    
    # Check that creation log exists
    log_path = p_dir / "policy_pr_creation_logs.jsonl"
    assert log_path.exists()

@patch("services.project_factory.policy_pr_creation_service.PolicyGitWorkspace")
@patch("services.project_factory.policy_pr_creation_service.PolicyGitHubPRAdapter")
def test_execute_policy_pr_creation_applies_modify_preview(mock_gh_adapter, mock_git_workspace, workspace_dir):
    mock_git_instance = mock_git_workspace.return_value
    mock_git_instance.commit.return_value = "mocksha123"

    mock_gh_instance = mock_gh_adapter.return_value
    mock_gh_instance.create_draft_pr.return_value = (True, "https://github.com/mock/pr/1", "")

    proposal_id = "POL-1234"
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    target_file = Path(workspace_dir) / "agents" / "policy.json"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text("{}\n", encoding="utf-8")

    with open(p_dir / "policy_draft_pr_plan.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "branch_name": "codex/policy-123",
            "target_branch": "main",
            "draft_title": "Update policy",
            "files_to_apply": ["agents/policy.json"],
            "git_operations_performed": False
        }, f)

    with open(p_dir / "policy_apply_preview.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "production_apply_performed": False,
            "policy_files_modified": False,
            "blocking_risks": [],
            "preview_changes": [
                {"change_type": "MODIFY", "target_file": "agents/policy.json"}
            ]
        }, f)

    pack_dir = p_dir / "policy_governance_evidence_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    with open(pack_dir / "policy_governance_manifest.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "ready_for_operator_pr_creation": True
        }, f)

    request = PolicyPRCreationRequest(
        operator_id="ADMIN",
        rationale="Approved",
        risk_acknowledgement=True,
        mode="safe_local_or_mock"
    )

    result = execute_policy_pr_creation(proposal_id, request, workspace_root=workspace_dir)

    assert result["modified_files"] == ["agents/policy.json"]
    assert "Added via Policy Autopilot POL-1234" in target_file.read_text(encoding="utf-8")
