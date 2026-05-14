import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Page, Response, BrowserContext
from services.observability.logging import get_logger

_log = get_logger("ui_evidence_runner")

class UIEvidenceRunner:
    def __init__(self, base_url: str = "http://localhost:3100"):
        self.base_url = base_url.rstrip("/")
        self.artifacts_dir = "artifacts/ui_repair/evidence"
        os.makedirs(self.artifacts_dir, exist_ok=True)

    @asynccontextmanager
    async def _get_context(self):
        """Exposes browser context for advanced scenarios."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                ignore_https_errors=True
            )
            try:
                yield browser, context
            finally:
                await browser.close()

    async def run_smoke_test(self, routes: List[str]) -> List[Dict[str, Any]]:
        """Runs smoke tests on a list of routes and collects evidence."""
        _log.info(f"Starting UI smoke run for {len(routes)} routes at {self.base_url}")
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Create context with tracing capability
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                ignore_https_errors=True
            )
            
            for route in routes:
                route_result = await self._test_route(context, route)
                results.append(route_result)
                
            await browser.close()
        return results

    async def _test_route(self, context, route: str) -> Dict[str, Any]:
        """Tests a single route and captures detailed evidence."""
        page = await context.new_page()
        full_url = f"{self.base_url}/{route.lstrip('/')}"
        
        console_errors = []
        page.on("console", lambda msg: console_errors.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }) if msg.type == "error" else None)
        
        network_errors = []
        page.on("requestfailed", lambda request: network_errors.append({
            "url": request.url,
            "error": request.failure
        }))
        
        # Track 404/500 responses from API or assets
        bad_responses = []
        page.on("response", lambda response: bad_responses.append({
            "url": response.url,
            "status": response.status,
            "statusText": response.status_text
        }) if response.status >= 400 else None)

        start_time = time.time()
        
        evidence = {
            "route": route,
            "status": "PASS",
            "http_status": 200,
            "blank_page_detected": False,
            "console_errors": [],
            "network_errors": [],
            "response_time_ms": 0,
            "screenshot_path": None,
            "trace_path": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            # Navigate to route
            # Start tracing per route if we want fine-grained traces
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            
            response = await page.goto(full_url, wait_until="networkidle", timeout=30000)
            evidence["http_status"] = response.status if response else 0
            
            # Blank page detection logic
            # 1. Body text length
            body_text = await page.inner_text("body")
            if len(body_text.strip()) < 100:
                evidence["blank_page_detected"] = True
                
            # 2. Check for common React error boundaries or blank shells
            # For Next.js/React, often a blank page has a <div id="__next"></div> with nothing inside.
            content_exists = await page.query_selector("main") or await page.query_selector("#__next > *")
            if not content_exists and not evidence["blank_page_detected"]:
                # If neither main nor child of next exists, likely blank or loading stuck
                evidence["blank_page_detected"] = True

            if evidence["http_status"] >= 400 or evidence["blank_page_detected"]:
                evidence["status"] = "FAIL"
            elif console_errors:
                # If there are console errors, we might still count as PASS but flag for review
                # Actually, according to requirements, console errors are a failure type
                evidence["status"] = "FAIL"

        except Exception as e:
            evidence["status"] = "FAIL"
            evidence["error_detail"] = str(e)
            evidence["http_status"] = 0

        evidence["response_time_ms"] = int((time.time() - start_time) * 1000)
        evidence["console_errors"] = console_errors
        evidence["network_errors"] = network_errors + bad_responses
        
        # If failed, capture artifacts
        if evidence["status"] == "FAIL":
            safe_route = route.replace("/", "_").strip("_") or "root"
            ts = int(time.time())
            
            # Screenshot
            screenshot_name = f"screenshot_{safe_route}_{ts}.png"
            screenshot_path = os.path.join(self.artifacts_dir, screenshot_name)
            await page.screenshot(path=screenshot_path)
            evidence["screenshot_path"] = screenshot_path
            
            # Trace
            trace_name = f"trace_{safe_route}_{ts}.zip"
            trace_path = os.path.join(self.artifacts_dir, trace_name)
            await context.tracing.stop(path=trace_path)
            evidence["trace_path"] = trace_path
        else:
            # Stop tracing without saving
            await context.tracing.stop()

    async def _analyze_page(self, page: Page, route: str) -> Dict[str, Any]:
        """Analyzes an already navigated page for evidence."""
        # This is a helper for advanced drills where navigation is handled externally
        # or where we want to analyze current state.
        # For now, we'll reuse the core logic from _test_route by wrapping it
        # but _test_route handles navigation itself.
        # So we implement a focused analysis here.
        
        start_time = time.time()
        evidence = {
            "route": route,
            "status": "PASS",
            "http_status": 200,
            "blank_page_detected": False,
            "console_errors": [],
            "network_errors": [],
            "response_time_ms": 0,
            "screenshot_path": None,
            "trace_path": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            body_text = await page.inner_text("body")
            if len(body_text.strip()) < 100:
                evidence["blank_page_detected"] = True
                
            content_exists = await page.query_selector("main") or await page.query_selector("#__next > *")
            if not content_exists and not evidence["blank_page_detected"]:
                evidence["blank_page_detected"] = True

            if evidence["blank_page_detected"]:
                evidence["status"] = "FAIL"
                evidence["failure_type"] = "BLANK_PAGE"
                evidence["severity"] = "CRITICAL"

        except Exception as e:
            evidence["status"] = "FAIL"
            evidence["error_detail"] = str(e)
            evidence["failure_type"] = "UNKNOWN"

        evidence["response_time_ms"] = int((time.time() - start_time) * 1000)
        return evidence
