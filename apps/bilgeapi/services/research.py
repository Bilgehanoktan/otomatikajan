import hashlib
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import httpx

from apps.bilgeapi.repositories.interface import ResearchRepository

logger = logging.getLogger("bilgeapi.research")


class WebSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform search and return list of result dicts."""
        pass


class SerperSearchProvider(WebSearchProvider):
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        from apps.bilgeapi.config import settings
        
        api_key = settings.BILGEAPI_SERPER_API_KEY
        if not api_key:
            raise ValueError(
                "Serper API key is missing. Please set BILGEAPI_SERPER_API_KEY or SERPER_API_KEY."
            )
            
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query, "num": max_results}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"Serper API returned status code {response.status_code}")
                    response.raise_for_status()
                
                data = response.json()
                organic = data.get("organic", [])
                
                results = []
                for item in organic[:max_results]:
                    pub_date = None
                    date_str = item.get("date", "")
                    if date_str:
                        pub_date = self._parse_date_string(date_str)
                        
                    results.append({
                        "url": item.get("link", ""),
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "content": item.get("snippet", ""),
                        "source_type": self._infer_source_type(item.get("link", "")),
                        "published_at": pub_date,
                        "is_vendor": False
                    })
                return results
        except Exception as e:
            logger.error(f"Serper search failed: {e.__class__.__name__}")
            raise e

    def _infer_source_type(self, url: str) -> str:
        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
        if "docs." in domain or "api." in domain or "developer." in domain:
            return "official_docs"
        if "github.com" in domain:
            if "/issues" in path or "/discussions" in path or "/pull" in path:
                return "maintainer_comment"
            return "official_github"
        if "stackoverflow.com" in domain:
            return "accepted_answer"
        if "medium.com" in domain or "blog" in domain or "dev.to" in domain:
            return "blog_medium"
        return "unknown_forum"

    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        import re
        date_str_clean = date_str.lower().strip()
        now = datetime.now(timezone.utc)
        
        # Match 'X days ago'
        match_days = re.search(r"(\d+)\s+days?\s+ago", date_str_clean)
        if match_days:
            days = int(match_days.group(1))
            return now - timedelta(days=days)
            
        # Match 'X weeks ago'
        match_weeks = re.search(r"(\d+)\s+weeks?\s+ago", date_str_clean)
        if match_weeks:
            weeks = int(match_weeks.group(1))
            return now - timedelta(weeks=weeks * 7)
            
        # Match 'X months ago'
        match_months = re.search(r"(\d+)\s+months?\s+ago", date_str_clean)
        if match_months:
            months = int(match_months.group(1))
            return now - timedelta(days=months * 30)
            
        # Match 'X years ago'
        match_years = re.search(r"(\d+)\s+years?\s+ago", date_str_clean)
        if match_years:
            years = int(match_years.group(1))
            return now - timedelta(days=years * 365)
            
        for fmt in ("%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"):
            try:
                clean_date = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
                dt = datetime.strptime(clean_date, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None


class MockSearchProvider(WebSearchProvider):
    def __init__(self, custom_results: Optional[List[Dict[str, Any]]] = None):
        self.custom_results = custom_results


    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if self.custom_results is not None:
            return self.custom_results[:max_results]

        # Standard mock data based on query keywords or defaults
        query_lower = query.lower()
        now = datetime.now(timezone.utc)

        if "memory leak" in query_lower:
            return [
                {
                    "url": "https://docs.python.org/3/library/gc.html",
                    "title": "Garbage Collector interface in Python",
                    "snippet": "Provides controls for python garbage collection, useful for tracking memory leaks and cycle references.",
                    "content": "Full text of Python GC docs about tracing uncollectable objects and memory leak investigations.",
                    "source_type": "official_docs",
                    "published_at": now,
                    "is_vendor": False
                },
                {
                    "url": "https://github.com/fastapi/fastapi/issues/1234",
                    "title": "Memory leak when using background tasks in FastAPI #1234",
                    "snippet": "Users report memory leak issues with background tasks when using specific dependency structures.",
                    "content": "Discussion thread on FastAPI issues: dependency injection inside tasks keeps references alive.",
                    "source_type": "maintainer_comment",
                    "published_at": now,
                    "is_vendor": True
                },
                {
                    "url": "https://stackoverflow.com/questions/456789/python-fastapi-memory-leak",
                    "title": "How to resolve memory leak in FastAPI middleware?",
                    "snippet": "Make sure database connections are closed properly. The accepted answer suggests wrapping in try/finally.",
                    "content": "Stackoverflow answer: close session to prevent memory leak, accepted answer with +120 votes.",
                    "source_type": "accepted_answer",
                    "published_at": now,
                    "is_vendor": False
                }
            ][:max_results]

        elif "connection pool" in query_lower:
            return [
                {
                    "url": "https://docs.sqlalchemy.org/en/20/core/pooling.html",
                    "title": "Connection Pooling in SQLAlchemy",
                    "snippet": "SQLAlchemy includes a connection pooling system integrated directly into the Engine.",
                    "content": "SQLAlchemy pool options: pool_size, max_overflow, pool_timeout. Recommended pool recycling for long sessions.",
                    "source_type": "official_docs",
                    "published_at": now,
                    "is_vendor": True
                },
                {
                    "url": "https://medium.com/engineering/postgres-connection-pooling-best-practices",
                    "title": "Postgres Connection Pooling Best Practices",
                    "snippet": "Tips on tuning PgBouncer, SQLAlchemy pool size, and max_connections in production environments.",
                    "content": "Medium blog post sharing production setups for managing database connections and scaling pg pool size.",
                    "source_type": "blog_medium",
                    "published_at": now,
                    "is_vendor": False
                }
            ][:max_results]

        # Default results
        return [
            {
                "url": "https://docs.python.org/3/howto/logging.html",
                "title": "Logging HOWTO - Python Documentation",
                "snippet": "Logging is a means of tracking events that happen when some software runs.",
                "content": "Official Python logging tutorial and reference.",
                "source_type": "official_docs",
                "published_at": now,
                "is_vendor": False
            },
            {
                "url": "https://github.com/pallets/click/issues/555",
                "title": "Unhandled exception with click parsing #555",
                "snippet": "Click throws unhandled exceptions under certain windows terminals.",
                "content": "Click issue thread regarding windows terminal encoding problems and click command line parser.",
                "source_type": "maintainer_comment",
                "published_at": now,
                "is_vendor": False
            },
            {
                "url": "https://someunknownforum.com/thread/789",
                "title": "Help with unhandled error in python",
                "snippet": "Any idea why this python script crashes with key error? Here is my trace.",
                "content": "Forum thread with random user posts talking about python KeyErrors and dictionary gets.",
                "source_type": "unknown_forum",
                "published_at": now,
                "is_vendor": False
            }
        ][:max_results]


class SourceTrustScorer:
    @staticmethod
    def calculate_score(
        url: str,
        source_type: Optional[str] = None,
        recency_days: Optional[int] = None,
        match_ratio: float = 0.0,
        is_vendor: bool = False
    ) -> float:
        """
        Calculate trust score (0.0 to 100.0) based on source type, recency, query match, and vendor relation.
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()
        fragment = parsed_url.fragment.lower()

        # 1. Base Score based on Source Type / Domain patterns
        base_score = 20.0  # Default: Unknown Forum

        # Match Official Docs
        official_doc_domains = {
            "python.org", "postgresql.org", "redis.io", "fastapi.tiangolo.com",
            "sqlalchemy.org", "pydantic.run", "alembic.sqlalchemy.org"
        }
        is_official_doc = (
            domain.startswith("docs.") or
            domain.startswith("api.") or
            domain.startswith("developer.") or
            any(d in domain for d in official_doc_domains) or
            source_type == "official_docs"
        )

        is_github = "github.com" in domain
        is_github_discussion_issue = is_github and (
            "/issues" in path or "/discussions" in path or "/pull" in path
        )

        is_blog = (
            "medium.com" in domain or
            domain.startswith("blog.") or
            "dev.to" in domain or
            source_type == "blog_medium"
        )

        if is_official_doc:
            base_score = 95.0
        elif is_github_discussion_issue:
            base_score = 85.0
            # Check for maintainer comment indicators
            if "comment" in fragment or "comment" in path or source_type == "maintainer_comment":
                base_score = 80.0
        elif source_type == "maintainer_comment":
            base_score = 80.0
        elif "stackoverflow.com" in domain:
            if "accepted" in fragment or "accepted=true" in url or source_type == "accepted_answer":
                base_score = 70.0
            else:
                base_score = 60.0
        elif is_blog:
            base_score = 35.0
        elif source_type == "unknown_forum":
            base_score = 20.0

        score = base_score

        # 2. Recency Adjustment (Güncellik)
        if recency_days is not None:
            if recency_days <= 365:  # <= 1 year
                score += 5.0
            elif recency_days > 1825:  # > 5 years
                score -= 20.0
            elif recency_days > 1095:  # > 3 years
                score -= 10.0

        # 3. Match Rate Adjustment (Uyuşma oranı)
        # Add up to +10.0 points depending on token match ratio
        score += match_ratio * 10.0

        # 4. Vendor Relationship (Vendor ilişkisi)
        if is_vendor:
            score += 5.0

        # Clamp between 0.0 and 100.0
        return max(0.0, min(100.0, score))


class WebResearchAdapter:
    def __init__(self, provider: WebSearchProvider, repo: ResearchRepository, ledger_service: Optional[Any] = None):
        self.provider = provider
        self.repo = repo
        self.ledger_service = ledger_service

    async def _append_ledger_event(self, *, request_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.ledger_service:
            return
        try:
            await self.ledger_service.append_event(
                chain_id=f"chain_{request_id}",
                event_type=event_type,
                entity_type="research_request",
                entity_id=request_id,
                actor_id=payload.get("tenant_id") or "system",
                payload=payload,
            )
        except Exception as exc:
            logger.warning("Review ledger append failed for research:%s: %s", request_id, exc)

    async def run_research(self, request_id: str) -> List[Dict[str, Any]]:
        """
        Execute search query variations, filter sources, grade them with SourceTrustScorer, and save evidences.
        """
        req = await self.repo.get_request(request_id)
        if not req:
            raise ValueError(f"Research request not found: {request_id}")

        await self.repo.update_request_status(request_id, "RUNNING")
        try:
            # Generate up to 3 queries
            queries = [
                req["query"],
                f"{req['query']} fix error",
                f"{req['query']} best practice"
            ]

            all_results = []
            for q in queries[:3]:
                results = await self.provider.search(q, max_results=5)
                all_results.extend(results)

            # Deduplicate by URL
            unique_results = {}
            for res in all_results:
                url = res.get("url")
                if url and url not in unique_results:
                    unique_results[url] = res

            # Limit to 5 sources (max_sources: 5)
            sources = list(unique_results.values())[:5]

            saved_evidences = []
            for src in sources:
                url = src.get("url")
                title = src.get("title", "")
                snippet = src.get("snippet", "")
                content = src.get("content", snippet)
                source_type = src.get("source_type")
                is_vendor = src.get("is_vendor", False)
                published_at = src.get("published_at")

                # Compute match ratio between request query and result title + snippet
                query_words = set(req["query"].lower().split())
                text_words = set((title + " " + snippet).lower().split())
                if query_words:
                    match_ratio = len(query_words & text_words) / len(query_words)
                else:
                    match_ratio = 0.0

                # Compute recency days
                recency_days = None
                if published_at:
                    if isinstance(published_at, str):
                        try:
                            published_at = datetime.fromisoformat(published_at)
                        except ValueError:
                            published_at = None
                    if isinstance(published_at, datetime):
                        if published_at.tzinfo is None:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        recency_days = (now - published_at).days

                # Score source trust
                trust_score = SourceTrustScorer.calculate_score(
                    url=url,
                    source_type=source_type,
                    recency_days=recency_days,
                    match_ratio=match_ratio,
                    is_vendor=is_vendor
                )

                # Generate content summary (Avoid storing full raw page to prevent DB bloat)
                summary = f"Summary of {title}: {snippet[:200]}"
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                parsed_url = urlparse(url)
                domain = parsed_url.netloc or "unknown"

                evidence_data = {
                    "research_id": request_id,
                    "source_url": url,
                    "source_domain": domain,
                    "title": title,
                    "snippet": snippet,
                    "raw_content_summary": summary,
                    "content_hash": content_hash,
                    "trust_score": trust_score,
                }

                ev = await self.repo.create_evidence(evidence_data)
                saved_evidences.append(ev)

            updated = await self.repo.update_request_status(request_id, "COMPLETED")
            await self._append_ledger_event(
                request_id=request_id,
                event_type="RESEARCH_COMPLETED",
                payload={
                    "request": updated or req,
                    "evidence_ids": [item["id"] for item in saved_evidences],
                    "evidence_count": len(saved_evidences),
                },
            )
            return saved_evidences

        except Exception as e:
            logger.error(f"Error executing research request {request_id}: {e}", exc_info=True)
            failed = await self.repo.update_request_status(request_id, "FAILED", error_message=str(e))
            await self._append_ledger_event(
                request_id=request_id,
                event_type="RESEARCH_FAILED",
                payload={"request": failed or req, "error": str(e)},
            )
            raise e
