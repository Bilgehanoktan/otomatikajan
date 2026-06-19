from playwright.sync_api import expect, sync_playwright
import time
import os


def test_websocket_reconnect():
    """
    E2E Playwright test validating UI auto-reconnect behaviors under connection losses.
    Simulates a total network blackout and restores it cleanly.
    """
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}"))

            page.add_init_script("""
                window.activeWebSockets = [];
                const OriginalWebSocket = window.WebSocket;
                window.OriginalWebSocket = OriginalWebSocket;

                window.WebSocketTracker = function(url, protocols) {
                    console.log("WebSocket constructor called with url:", url);
                    if (!url || typeof url !== "string") {
                        return protocols !== undefined ? new OriginalWebSocket(url, protocols) : new OriginalWebSocket(url);
                    }
                    try {
                        const ws = protocols !== undefined ? new OriginalWebSocket(url, protocols) : new OriginalWebSocket(url);
                        window.activeWebSockets.push(ws);
                        return ws;
                    } catch (e) {
                        return protocols !== undefined ? new OriginalWebSocket(url, protocols) : new OriginalWebSocket(url);
                    }
                };
                window.WebSocketTracker.prototype = OriginalWebSocket.prototype;
                window.WebSocket = window.WebSocketTracker;
            """)

            in_container = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER", "").strip().lower() in {"1", "true", "yes", "on"}
            target_url = "http://cms:3100/" if in_container else "http://localhost:3100/"
            page.goto(target_url)

            status_badge = page.locator("div.ml-auto.px-2\\.5.py-1").first
            expect(status_badge).to_be_visible(timeout=10000)

            stable_established = False
            for _ in range(40):
                status_text = status_badge.inner_text()
                if any(x in status_text.upper() for x in ["STABLE", "KARARLI", "STABÄ°L"]):
                    stable_established = True
                    break
                time.sleep(0.5)

            print(f"[E2E Test] Initial Established Status: {status_badge.inner_text()}")
            assert stable_established, "WebSocket connection failed to establish stable state within timeout."

            print("[E2E Test] Simulating connection loss (blocking all new WebSockets)...")
            page.evaluate("""
                window.WebSocket = function() {
                    throw new Error("Network Blackout: Connection refused");
                };

                window.activeWebSockets.forEach(ws => {
                    try {
                        ws.close();
                    } catch (e) {}
                });
            """)

            time.sleep(1.5)

            offline_status_text = status_badge.inner_text()
            print(f"[E2E Test] Degraded WebSocket Status: {offline_status_text}")
            assert any(x in offline_status_text.upper() for x in ["FALLBACK", "KAYIP", "LOST"])
            assert not any(x in offline_status_text.upper() for x in ["STABLE", "KARARLI", "STABÄ°L"])

            print("[E2E Test] Restoring connection (unblocking WebSockets)...")
            page.evaluate("""
                window.activeWebSockets = [];
                window.WebSocket = window.WebSocketTracker;
                void 0;
            """)

            reconnected = False
            for _ in range(120):
                status_text = status_badge.inner_text()
                if any(x in status_text.upper() for x in ["STABLE", "SYNC", "KARARLI", "SENKRONIZE", "STABÄ°L"]):
                    reconnected = True
                    break
                time.sleep(0.5)

            ws_states = page.evaluate("""
                window.activeWebSockets.map(ws => ({
                    url: ws.url,
                    readyState: ws.readyState,
                }))
            """)
            print("[E2E Test] WS states in browser:", ws_states)

            reconnected_status_text = status_badge.inner_text()
            print(f"[E2E Test] Reconnected WebSocket Status: {reconnected_status_text}")
            assert reconnected, "WebSocket connection failed to re-establish stable state within timeout."
        finally:
            browser.close()
