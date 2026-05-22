import pytest
from unittest.mock import MagicMock
from services.project_factory.models import DraftPrCreateRequest, ProjectFactoryIntake, RequirementGate
from services.project_factory.pr_creation_service import execute_pr_creation
from services.project_factory.git_workspace import GitSafetyViolation
from services.project_factory.github_pr_adapter import GitHubRemoteUnavailable

def test_execute_pr_creation_success(monkeypatch, tmp_path):
    # Mock artifacts
    brief = ProjectFactoryIntake(
        project_id="PF-1", source_suggestion_id="1", audit_run_id="2",
        title="Title", problem_statement="P", recommended_action="R"
    )
    gate = RequirementGate()
    
    monkeypatch.setattr("services.project_factory.pr_creation_service.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_creation_service.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_creation_service.write_draft_pr_creation", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_creation_service.record_pr_creation_decision", lambda **kwargs: None)
    
    # Mock validate_pr_creation_safety
    monkeypatch.setattr("services.project_factory.pr_creation_service.validate_pr_creation_safety", lambda **k: {
        "draft_pr_plan": {"branch_name": "codex/pf-1", "target_branch": "main", "files_to_apply": ["a.txt"]}
    })
    
    # Mock GitWorkspaceExecutor
    mock_git = MagicMock()
    mock_git.commit_changes.return_value = "sha123"
    monkeypatch.setattr("services.project_factory.pr_creation_service.GitWorkspaceExecutor", lambda **k: mock_git)
    
    # Mock create_draft_pr
    monkeypatch.setattr("services.project_factory.pr_creation_service.create_draft_pr", lambda **k: ("https://github.com/a/b/pull/1", "DRAFT_PR_CREATED"))
    
    req = DraftPrCreateRequest(operator_id="op", rationale="looks good", risk_acknowledgement=True)
    res = execute_pr_creation("PF-1", req, str(tmp_path))
    
    assert res.status == "PR_CREATED_WAITING_REVIEW"
    assert res.pr_url == "https://github.com/a/b/pull/1"
    assert res.commit_sha == "sha123"
    assert brief.status == "PR_CREATED_WAITING_REVIEW"

def test_execute_pr_creation_github_unavailable(monkeypatch, tmp_path):
    brief = ProjectFactoryIntake(
        project_id="PF-1", source_suggestion_id="1", audit_run_id="2",
        title="Title", problem_statement="P", recommended_action="R"
    )
    gate = RequirementGate()
    monkeypatch.setattr("services.project_factory.pr_creation_service.load_project_factory_artifacts", lambda p, r: (brief, gate))
    monkeypatch.setattr("services.project_factory.pr_creation_service.write_project_factory_artifacts", lambda b, g, r: None)
    monkeypatch.setattr("services.project_factory.pr_creation_service.write_draft_pr_creation", lambda p, d, r: None)
    monkeypatch.setattr("services.project_factory.pr_creation_service.record_pr_creation_decision", lambda **kwargs: None)
    
    monkeypatch.setattr("services.project_factory.pr_creation_service.validate_pr_creation_safety", lambda **k: {
        "draft_pr_plan": {"branch_name": "codex/pf-1", "target_branch": "main", "files_to_apply": ["a.txt"]}
    })
    
    mock_git = MagicMock()
    monkeypatch.setattr("services.project_factory.pr_creation_service.GitWorkspaceExecutor", lambda **k: mock_git)
    
    def raise_ghe(**k):
        raise GitHubRemoteUnavailable("No token")
    monkeypatch.setattr("services.project_factory.pr_creation_service.create_draft_pr", raise_ghe)
    
    req = DraftPrCreateRequest(operator_id="op", rationale="looks good", risk_acknowledgement=True)
    res = execute_pr_creation("PF-1", req, str(tmp_path))
    
    assert res.status == "PR_CREATION_BLOCKED"
    assert not res.pr_url
