import pytest
from unittest.mock import MagicMock
from services.project_factory.github_pr_adapter import create_draft_pr, GitHubRemoteUnavailable
import httpx

def test_create_draft_pr_missing_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(GitHubRemoteUnavailable, match="GITHUB_TOKEN environment variable is not set"):
        create_draft_pr("Title", "Body", "head", "base")

def test_create_draft_pr_success(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake_token")
    
    mock_post = MagicMock()
    mock_post.return_value.json.return_value = {"html_url": "https://github.com/org/repo/pull/1"}
    mock_post.return_value.raise_for_status = MagicMock()
    monkeypatch.setattr(httpx, "post", mock_post)

    url, status = create_draft_pr("T", "B", "codex/h", "main", "org", "repo")
    assert url == "https://github.com/org/repo/pull/1"
    assert status == "DRAFT_PR_CREATED"
    
    # Verify payload format
    call_args = mock_post.call_args
    assert call_args[1]["json"]["draft"] is True
    assert call_args[1]["json"]["head"] == "codex/h"

def test_create_draft_pr_http_error(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake_token")
    
    def raise_err(*args, **kwargs):
        raise httpx.RequestError("Network timeout")
        
    monkeypatch.setattr(httpx, "post", raise_err)

    with pytest.raises(GitHubRemoteUnavailable, match="Network error"):
        create_draft_pr("T", "B", "codex/h", "main", "org", "repo")
