from playwright.async_api import Page, Route
import json

class CacheChaosAdapter:
    """Simulates stale cache or cache corruption."""
    
    def __init__(self, page: Page):
        self.page = page

    async def inject_stale_data(self, url_pattern: str, stale_json: dict):
        """Intercepts an API call and returns stale data."""
        async def handle_route(route: Route):
            await route.fulfill(
                status=200,
                body=json.dumps(stale_json),
                headers={"X-Chaos-Stale": "true", "Content-Type": "application/json"}
            )
        await self.page.context.route(url_pattern, handle_route)

    async def clear_cache(self):
        """Clears browser cache and service workers via script."""
        await self.page.evaluate('''async () => {
            if ('serviceWorker' in navigator) {
                const registrations = await navigator.serviceWorker.getRegistrations();
                for (let registration of registrations) {
                    await registration.unregister();
                }
            }
            const cachesKeys = await caches.keys();
            for (let key of cachesKeys) {
                await caches.delete(key);
            }
        }''')

    async def clear_chaos(self):
        await self.page.context.unroute("**/*")
