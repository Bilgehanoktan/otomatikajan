from abc import ABC, abstractmethod
from typing import List
import base64
import logging
import uuid
import httpx

logger = logging.getLogger(__name__)


class BaseGitHubPrAdapter(ABC):
    @abstractmethod
    async def create_draft_pr(self, title: str, body: str, branch_name: str, patch_code: str, affected_files: List[str]) -> str:
        """Create a draft PR and return the PR URL."""
        pass


class MockGitHubPrAdapter(BaseGitHubPrAdapter):
    async def create_draft_pr(self, title: str, body: str, branch_name: str, patch_code: str, affected_files: List[str]) -> str:
        logger.info(f"Mock creating draft PR: '{title}' on branch '{branch_name}'")
        return f"https://github.com/mock-owner/mock-repo/pull/{uuid.uuid4().hex[:4]}"


class GitHubDraftPrAdapter(BaseGitHubPrAdapter):
    def __init__(self, token: str, owner: str, repo: str, base_branch: str = "main", allow_real: bool = False):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_branch = base_branch
        self.allow_real = allow_real

    async def create_draft_pr(self, title: str, body: str, branch_name: str, patch_code: str, affected_files: List[str]) -> str:
        if not self.allow_real:
            logger.info("Real Draft PR is disabled (allow_real=False). Falling back to mock URL.")
            return f"https://github.com/{self.owner}/{self.repo}/pull/mock-{uuid.uuid4().hex[:4]}"

        if not self.token or not self.owner or not self.repo:
            raise ValueError("GitHub token, owner, and repo must be configured for real PR creation.")

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        async with httpx.AsyncClient() as client:
            base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

            # 1. Get base branch ref sha
            ref_res = await client.get(f"{base_url}/git/ref/heads/{self.base_branch}", headers=headers)
            if ref_res.status_code != 200:
                raise Exception(f"Failed to fetch base branch ref: {ref_res.text}")
            
            base_sha = ref_res.json()["object"]["sha"]

            # 2. Create new branch
            create_ref_payload = {
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
            ref_create_res = await client.post(f"{base_url}/git/refs", headers=headers, json=create_ref_payload)
            if ref_create_res.status_code not in (201, 422): # 422 means ref already exists
                raise Exception(f"Failed to create new branch: {ref_create_res.text}")

            # 3. Create or update the patch file in the new branch
            patch_file_path = f"patches/{branch_name}.patch"
            sha_opt = None
            file_res = await client.get(f"{base_url}/contents/{patch_file_path}?ref={branch_name}", headers=headers)
            if file_res.status_code == 200:
                sha_opt = file_res.json()["sha"]

            commit_file_payload = {
                "message": f"Add autonomous patch: {title}",
                "content": base64.b64encode(patch_code.encode("utf-8")).decode("utf-8"),
                "branch": branch_name
            }
            if sha_opt:
                commit_file_payload["sha"] = sha_opt

            commit_res = await client.put(f"{base_url}/contents/{patch_file_path}", headers=headers, json=commit_file_payload)
            if commit_res.status_code not in (200, 201):
                raise Exception(f"Failed to commit patch file: {commit_res.text}")

            # 4. Create Draft PR
            pr_payload = {
                "title": title,
                "body": body,
                "head": branch_name,
                "base": self.base_branch,
                "draft": True
            }
            pr_res = await client.post(f"{base_url}/pulls", headers=headers, json=pr_payload)
            if pr_res.status_code != 201:
                raise Exception(f"Failed to create draft PR: {pr_res.text}")

            pr_data = pr_res.json()
            return pr_data["html_url"]
