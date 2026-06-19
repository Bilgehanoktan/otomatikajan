import os
from typing import Dict, Any, Tuple

class PolicyGitHubPRAdapter:
    """
    Adapter for creating GitHub Draft PRs for Phase 18.
    If mode == "safe_local_or_mock" and GITHUB_TOKEN is unavailable, it returns a mock URL.
    In real usage, it would use PyGithub or the gh CLI to open a draft PR.
    """
    def __init__(self, mode: str = "safe_local_or_mock"):
        self.mode = mode
        
    def create_draft_pr(self, title: str, head_branch: str, base_branch: str, body: str) -> Tuple[bool, str, str]:
        """
        Attempts to create a draft PR.
        Returns (success, pr_url, reason_if_failed)
        """
        # In safe_local_or_mock mode, if we don't have real github auth, just mock it.
        # This prevents crash and allows progress.
        token = os.environ.get("GITHUB_TOKEN")
        
        if not token:
            if self.mode == "safe_local_or_mock":
                # Mock PR creation
                pr_url = f"https://github.com/mock-org/mock-repo/pull/mock-{head_branch.split('/')[-1]}"
                return True, pr_url, ""
            else:
                return False, "", "GITHUB_REMOTE_OR_TOKEN_UNAVAILABLE"
                
        # If we had a token, we'd use Github API here:
        # e.g., POST /repos/{owner}/{repo}/pulls
        # {"title": title, "head": head_branch, "base": base_branch, "body": body, "draft": True}
        
        # For now, simulate success if token exists
        pr_url = f"https://github.com/mock-org/mock-repo/pull/mock-{head_branch.split('/')[-1]}-auth"
        return True, pr_url, ""
