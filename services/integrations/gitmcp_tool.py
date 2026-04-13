import os
import httpx
import logging
from typing import Dict, Any, Optional, List
from services.observability.logging import get_logger

logger = get_logger("tools.gitmcp")

class GitMCPTool:
    """
    GitMCP (gitmcp.io) entegrasyon aracı.
    GitHub depolarını MCP (Model Context Protocol) bağlamında okumayı sağlar.
    """
    def __init__(self, base_url: str = "https://gitmcp.io"):
        self.base_url = base_url.rstrip("/")

    async def get_repo_context(self, repo_path: str, format: str = "llms.txt") -> str:
        """
        Herhangi bir GitHub deposundan structured context okur.
        Format seçenekleri: 'llms.txt', 'llms-full.txt', 'README.md'
        """
        url = f"{self.base_url}/{repo_path}/{format}"
        logger.info(f"GitMCP: Context isteniyor: {url}")
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, timeout=15.0)
                if response.status_code == 200:
                    return response.text
                return f"Hata: {response.status_code}"
        except Exception as e:
            return f"İstisna: {str(e)}"

    async def get_raw_file(self, repo_path: str, file_path: str) -> str:
        """
        GitMCP üzerinden bir dosyanın içeriğini ham (raw) olarak çekmeyi simüle eder.
        """
        url = f"{self.base_url}/{repo_path}/blob/main/{file_path}"
        logger.info(f"GitMCP: Ham dosya isteniyor: {url}")
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    return response.text
                return f"Dosya alınamadı: {response.status_code}"
        except Exception as e:
            return str(e)

    async def get_repo_tree(self, repo_path: str) -> List[str]:
        """Repo yapısını (dosya listesini) çeker."""
        import re
        context = await self.get_repo_context(repo_path, "llms.txt")
        files = re.findall(r"-\s\[.*?\]\((.*?)\)", context)
        return files or ["Repo yapısı llms.txt üzerinden çözümlenemedi."]

def get_gitmcp_tool() -> GitMCPTool:
    return GitMCPTool()
