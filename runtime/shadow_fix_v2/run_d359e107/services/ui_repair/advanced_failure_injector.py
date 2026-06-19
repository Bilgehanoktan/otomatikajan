from typing import Optional, Dict, Any
from playwright.async_api import BrowserContext, Page
from .network_chaos_adapter import NetworkChaosAdapter
from .browser_chaos_adapter import BrowserChaosAdapter
from .websocket_chaos_adapter import WebSocketChaosAdapter
from .cache_chaos_adapter import CacheChaosAdapter

class AdvancedFailureInjector:
    """Orchestrates multiple chaos adapters for advanced failure injection."""
    
    def __init__(self, context: BrowserContext, page: Page):
        self.context = context
        self.page = page
        self.network = NetworkChaosAdapter(context)
        self.browser = BrowserChaosAdapter(context)
        self.websocket = WebSocketChaosAdapter(page)
        self.cache = CacheChaosAdapter(page)

    async def inject(self, chaos_type: str, config: Dict[str, Any]):
        """Injects failure based on type and config."""
        
        if chaos_type == "NETWORK_LATENCY":
            await self.network.inject_latency(
                config.get("target_api", "**/*"), 
                config.get("latency_ms", 1000)
            )
        elif chaos_type == "NETWORK_TIMEOUT":
            await self.network.inject_timeout(config.get("target_api", "**/*"))
        elif chaos_type == "API_ERROR":
            await self.network.inject_status(
                config.get("target_api", "**/*"), 
                config.get("status", 500)
            )
        elif chaos_type == "JS_CHUNK_BLOCK":
            await self.browser.block_resources(config.get("pattern", "**/*.js"))
        elif chaos_type == "CSS_BLOCK":
            await self.browser.block_resources(config.get("pattern", "**/*.css"))
        elif chaos_type == "WEBSOCKET_DROP":
            await self.websocket.drop_connections()
        elif chaos_type == "STALE_CACHE":
            await self.cache.inject_stale_data(
                config.get("target_api", "**/*"),
                config.get("stale_data", {})
            )
        # Add more as needed

    async def cleanup(self):
        """Clears all injected chaos."""
        await self.network.clear_chaos()
        await self.browser.clear_chaos()
        await self.websocket.clear_chaos()
        await self.cache.clear_chaos()
