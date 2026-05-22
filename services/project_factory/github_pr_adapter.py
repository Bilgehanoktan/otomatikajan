import os
import httpx
from typing import Dict, Any, Tuple

class GitHubRemoteUnavailable(Exception):
    pass

def create_draft_pr(
    title: str,
    body: str,
    head_branch: str,
    base_branch: str,
    repo_owner: str = "",
    repo_name: str = ""
) -> Tuple[str, str]:
    """
    Creates a draft PR on GitHub.
    Returns (pr_url, status).
    Raises GitHubRemoteUnavailable if GitHub token is missing or if the API call fails.
    """
    github_token = os.environ.get("GITHUB_TOKEN")
    
    if not github_token:
        raise GitHubRemoteUnavailable("GITHUB_TOKEN environment variable is not set.")

    # Try to extract repo_owner and repo_name from origin remote if not provided
    if not repo_owner or not repo_name:
        try:
            import subprocess
            res = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                stdout=subprocess.PIPE,
                text=True,
                check=True
            )
            url = res.stdout.strip()
            # Parse git@github.com:owner/repo.git or https://github.com/owner/repo.git
            if url.startswith("git@github.com:"):
                parts = url.split(":")[1].replace(".git", "").split("/")
                repo_owner, repo_name = parts[0], parts[1]
            elif "github.com/" in url:
                parts = url.split("github.com/")[1].replace(".git", "").split("/")
                repo_owner, repo_name = parts[0], parts[1]
            else:
                raise GitHubRemoteUnavailable("Could not parse GitHub origin URL.")
        except Exception:
            raise GitHubRemoteUnavailable("Could not determine repository owner/name from origin remote.")

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch,
        "draft": True
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return data.get("html_url", ""), "DRAFT_PR_CREATED"
    except httpx.HTTPStatusError as e:
        raise GitHubRemoteUnavailable(f"GitHub API Error: {e.response.text}")
    except Exception as e:
        raise GitHubRemoteUnavailable(f"Network error when calling GitHub API: {e}")
