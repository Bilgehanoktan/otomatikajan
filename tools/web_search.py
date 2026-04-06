import os
import httpx
from typing import Dict, Any, List
from packages.packages.observability.logging import get_logger

logger = get_logger("tools.web_search")

class WebSearchTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev/search"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("SERPER_API_KEY eksik, arama yapılamıyor.")
            return []

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, headers=headers, json=payload, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("organic", [])[:5]:
                    results.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet")
                    })
                return results
        except Exception as e:
            logger.error(f"Web search hatası: {e}")
            return []

def get_web_search() -> WebSearchTool:
    return WebSearchTool()
