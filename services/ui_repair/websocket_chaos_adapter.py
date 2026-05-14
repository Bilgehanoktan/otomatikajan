from playwright.async_api import Page

class WebSocketChaosAdapter:
    """Simulates WebSocket interruptions."""
    
    def __init__(self, page: Page):
        self.page = page

    async def drop_connections(self):
        """Finds active WebSockets and closes them via client-side script."""
        await self.page.evaluate('''() => {
            // This is a heuristic to find common WebSocket objects if exposed, 
            // but usually we intercept the constructor if we want full control.
            // For simple chaos, we can try to find active ones or just block the endpoint.
            console.log("Chaos: Dropping WebSockets...");
            if (window.activeSockets) {
                window.activeSockets.forEach(s => s.close());
            }
        }''')

    async def block_handshake(self, url_pattern: str):
        """Blocks new WebSocket handshakes."""
        # Note: Playwright doesn't always intercept 'websocket' in route()
        # but it works for the initial HTTP upgrade request.
        await self.page.context.route(url_pattern, lambda route: route.abort("connectionfailed"))

    async def clear_chaos(self):
        await self.page.context.unroute("**/*")
