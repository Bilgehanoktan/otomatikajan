import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import BrowserContext, Route

class NetworkChaosAdapter:
    """Injects network-level failures using Playwright route interception."""
    
    def __init__(self, context: BrowserContext):
        self.context = context
        self.active_intercepts = []

    async def inject_latency(self, url_pattern: str, delay_ms: int):
        """Injects artificial delay into matching requests."""
        async def handle_route(route: Route):
            await asyncio.sleep(delay_ms / 1000.0)
            await route.continue_()
            
        await self.context.route(url_pattern, handle_route)
        self.active_intercepts.append(url_pattern)

    async def inject_timeout(self, url_pattern: str):
        """Simulates a request timeout by never resolving the route."""
        async def handle_route(route: Route):
            # We just let it hang or abort with timeout
            await route.abort("timedout")
            
        await self.context.route(url_pattern, handle_route)
        self.active_intercepts.append(url_pattern)

    async def inject_status(self, url_pattern: str, status: int):
        """Injects a specific HTTP status code."""
        await self.context.route(url_pattern, lambda route: route.fulfill(status=status))
        self.active_intercepts.append(url_pattern)

    async def inject_malformed_json(self, url_pattern: str):
        """Injects invalid JSON response."""
        await self.context.route(
            url_pattern, 
            lambda route: route.fulfill(status=200, body='{"error": "incomplete', content_type="application/json")
        )
        self.active_intercepts.append(url_pattern)

    async def inject_cors_failure(self, url_pattern: str):
        """Simulates CORS failure by removing headers."""
        async def handle_route(route: Route):
            await route.fulfill(
                status=200,
                headers={"Access-Control-Allow-Origin": "null"}
            )
        await self.context.route(url_pattern, handle_route)
        self.active_intercepts.append(url_pattern)

    async def clear_chaos(self):
        """Removes all network intercepts."""
        await self.context.unroute("**/*")
        self.active_intercepts = []
