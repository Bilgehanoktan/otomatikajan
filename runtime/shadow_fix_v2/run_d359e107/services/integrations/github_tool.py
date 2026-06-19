import os
import httpx
from typing import Dict, Any, Optional
from services.observability.logging import get_logger
from services.integrations.base import BaseIntegrationTool, async_retry

logger = get_logger("tools.github")

class GitHubTool(BaseIntegrationTool):
    def __init__(self, token: str = None, repo: str = None):
        super().__init__(tool_name="github")
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPO")
        self.base_url = f"https://api.github.com/repos/{self.repo}"

    async def call(self, action: str, **kwargs) -> Any:
        if action == "create_pull_request":
            return await self.create_pull_request(**kwargs)
        return None

    @async_retry(max_retries=2, backoff=2.0)
    async def create_pull_request(self, head: str, title: str, body: str, base: str = "main") -> Optional[Dict[str, Any]]:
        """Ajan tarafından onarılan kodun PR olarak açılmasını sağlar."""
        if not self.token or not self.repo:
            logger.warning("GITHUB_TOKEN veya GITHUB_REPO eksik.")
            return None

        url = f"{self.base_url}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=10.0)
                if response.status_code == 201:
                    logger.info(f"GitHub: PR başarıyla açıldı: {title}")
                    return response.json()
                elif response.status_code == 422:
                    logger.warning(f"GitHub: PR zaten mevcut veya dal hatalı: {response.text}")
                    return None
                else:
                    logger.error(f"GitHub PR hatası ({response.status_code}): {response.text}")
                    return None
        except Exception as e:
            logger.error(f"GitHub PR istisnası: {e}")
            return None

def get_github_tool() -> GitHubTool:
    return GitHubTool()
