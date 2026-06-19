"""
Sovereign AGI — Phase 19 (L5 Autonomy)
services/repair/infrastructure/github_intel.py
Global Intelligence Module. Fetches contextual error solutions from GitHub Issues to stop LLM hallucination.
"""

import aiohttp
import urllib.parse
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class GitHubIntelAnalyzer:
    """
    Given a stack trace or an error message, finds related Closed Issues in GitHub
    that contain code patches, thereby guiding the local CodeRepairStrategy.
    """
    def __init__(self, github_token: str = None):
        # Allow default operation even without token (rate limited)
        from libs.config import GITHUB_TOKEN
        self.token = github_token or GITHUB_TOKEN
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def extract_search_query(self, error_trace: str) -> str:
        """
        Removes file paths and local variable noise from trace to get a generic search query.
        """
        # Take the last line of the exception (usually ErrorType: Message)
        lines = error_trace.strip().split('\n')
        if not lines:
            return ""
            
        last_line = lines[-1]
        
        # Strip long hex IDs, file paths or explicit line numbers from the query
        clean_query = re.sub(r'0x[a-fA-F0-9]+', '', last_line)
        clean_query = re.sub(r'/[A-Za-z0-9_./-]+', '', clean_query)
        
        # E.g. "TypeError: 'NoneType' object is not iterable"
        return clean_query[:100]

    async def fetch_issue_context(self, error_trace: str) -> str:
        """
        Returns a formatted context string containing solutions from the real world.
        """
        query = self.extract_search_query(error_trace)
        if not query or len(query) < 5:
            return "[GitHub Intel: Trace too short to analyze]"
            
        repo_filter = "language:python is:closed"
        q = urllib.parse.quote(f'"{query}" {repo_filter}')
        url = f"https://api.github.com/search/issues?q={q}&sort=relevance&per_page=3"

        intel_context = [f"--- GITHUB INTELLIGENCE REPORT ---"]
        intel_context.append(f"Searched for: {query}\n")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get("items", [])
                        if not items:
                            return "[GitHub Intel: No exact matches found in public repos.]"
                            
                        for item in items:
                            title = item.get("title", "")
                            body = item.get("body", "") or ""
                            # Snip body to prevent context explosion
                            snip = body[:400] + "..." if len(body) > 400 else body
                            intel_context.append(f"Issue: {title}\nContent:\n{snip}\n---")
                            
                        return "\n".join(intel_context)
                    else:
                        logger.warning(f"GitHub API Error: {resp.status}")
                        return f"[GitHub Intel: API unreachable ({resp.status})]"
        except Exception as e:
            logger.error(f"Error fetching GitHub intel: {e}")
            return f"[GitHub Intel: Network error - {e}]"
