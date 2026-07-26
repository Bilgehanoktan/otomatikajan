from playwright.sync_api import Page, expect
import time
import os

def test_websocket_reconnect(page: Page):
    """
    E2E Playwright test validating UI auto-reconnect behaviors under connection losses.
    Simulates a total network blackout and restores it cleanly.
    """
    # Listen to console events
    page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}"))

    # Inject a monkeypatch script to track created WebSocket instances
    page.add_init_script("""
        window.activeWebSockets = [];
        const OriginalWebSocket = window.WebSocket;
        window.OriginalWebSocket = OriginalWebSocket; // Keep reference to raw WebSocket
        
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

    # Navigate to the Refine control plane dashboard
    in_container = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER", "").strip().lower() in {"1", "true", "yes", "on"}
    target_url = "http://cms:3100/" if in_container else "http://localhost:3100/"
    page.goto(target_url)
    
    # Locate the telemetry status badge on the dashboard
    status_badge = page.locator('[data-testid="telemetry-status-badge"], div.ml-auto.px-2\\.5.py-1').first
    expect(status_badge).to_be_visible(timeout=10000)
    
    # Wait for the WebSocket connection to stabilize (change from SYNC to STABLE)
    stable_established = False
    for _ in range(40):
        status_text = status_badge.inner_text()
        if any(x in status_text.upper() for x in ["STABLE", "KARARLI", "STABİL"]):
            stable_established = True
            break
        time.sleep(0.5)
        
    print(f"[E2E Test] Initial Established Status: {status_badge.inner_text()}")
    assert stable_established, "WebSocket connection failed to establish stable state within timeout."
    
    # Simulate network connection loss (network blackout) by blocking constructor and closing active ones
    print("[E2E Test] Simulating connection loss (blocking all new WebSockets)...")
    page.evaluate("""
        // Monkeypatch to block all new connections instantly
        window.WebSocket = function() {
            throw new Error("Network Blackout: Connection refused");
        };
        
        // Terminate all active connections to trigger recovery loop
        window.activeWebSockets.forEach(ws => {
            try {
                ws.close();
            } catch (e) {}
        });
    """)
    
    # Wait for the recovery loop to run through all candidates and transition to polling fallback state
    time.sleep(1.5)
    
    # Assert that the UI reflects the degraded state (non-STABLE / fallback / lost)
    offline_status_text = status_badge.inner_text()
    print(f"[E2E Test] Degraded WebSocket Status: {offline_status_text}")
    assert any(x in offline_status_text.upper() for x in ["FALLBACK", "KAYIP", "LOST"])
    assert not any(x in offline_status_text.upper() for x in ["STABLE", "KARARLI", "STABİL"])
    
    # Restore the network connection (unblock WebSocket constructor)
    print("[E2E Test] Restoring connection (unblocking WebSockets)...")
    page.evaluate("""
        window.activeWebSockets = [];
        window.WebSocket = window.WebSocketTracker;
        void 0;
    """)
    
    # Wait for the auto-reconnection loop to establish standard link again
    reconnected = False
    for _ in range(120):
        status_text = status_badge.inner_text()
        if any(x in status_text.upper() for x in ["STABLE", "SYNC", "KARARLI", "SENKRONIZE", "STABİL"]):
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


