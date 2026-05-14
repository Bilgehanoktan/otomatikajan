from playwright.async_api import BrowserContext, Route

class BrowserChaosAdapter:
    """Injects browser-level failures like resource blocking."""
    
    def __init__(self, context: BrowserContext):
        self.context = context

    async def block_resources(self, pattern: str):
        """Blocks resources matching the pattern (e.g. *.js, *.css)."""
        await self.context.route(pattern, lambda route: route.abort("blockedbyclient"))

    async def inject_script_error(self, url_pattern: str):
        """Injects a script that throws an error when loaded."""
        await self.context.route(
            url_pattern, 
            lambda route: route.fulfill(
                status=200, 
                body="throw new Error('Chaos: Injected JS Failure');",
                content_type="application/javascript"
            )
        )

    async def clear_chaos(self):
        """Removes all browser-level blocks."""
        await self.context.unroute("**/*")
