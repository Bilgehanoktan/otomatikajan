import os
import logging
import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

from .ui_evidence_models import UIEvidencePack, UIEvidenceRequest, UIConsoleLog

logger = logging.getLogger(__name__)

class UIEvidenceRunner:
    """
    UI Evidence Runner — Playwright kullanarak UI kanıtlarını (screenshot, trace, log) toplar.
    """

    def __init__(self, base_output_dir: str = "repair_outputs"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    async def capture_evidence(self, request: UIEvidenceRequest) -> UIEvidencePack:
        """
        Belirtilen URL için UI kanıtlarını toplar.
        """
        case_dir = self.base_output_dir / request.case_id / "evidence"
        case_dir.mkdir(parents=True, exist_ok=True)

        if async_playwright is None:
            logger.warning("Playwright not installed, returning mock evidence.")
            return self.get_mock_evidence(request.case_id)

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as exc:
                logger.warning("Playwright browser unavailable, returning degraded mock evidence: %s", exc)
                evidence = self.get_mock_evidence(request.case_id)
                evidence.page_url = request.target_url
                evidence.metadata = {
                    **(evidence.metadata or {}),
                    "degraded": True,
                    "fallback_reason": "playwright_browser_unavailable",
                    "error": str(exc),
                }
                return evidence
            
            # Context settings for tracing
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                record_video_dir=str(case_dir / "videos") if request.capture_screenshot else None # Simplification
            )

            if request.capture_trace:
                await context.tracing.start(screenshots=True, snapshots=True, sources=True)

            page = await context.new_page()
            console_logs = []

            # Console log listener
            if request.capture_console:
                page.on("console", lambda msg: console_logs.append(
                    UIConsoleLog(
                        level=msg.type,
                        message=msg.text,
                        timestamp=datetime.now(timezone.utc)
                    )
                ))

            try:
                await page.goto(request.target_url, wait_until="networkidle", timeout=request.timeout_ms)
                
                screenshot_path = None
                if request.capture_screenshot:
                    screenshot_name = f"screenshot_{int(datetime.now(timezone.utc).timestamp())}.png"
                    screenshot_path = str(case_dir / screenshot_name)
                    await page.screenshot(path=screenshot_path, full_page=True)

                trace_path = None
                if request.capture_trace:
                    trace_name = f"trace_{int(datetime.now(timezone.utc).timestamp())}.zip"
                    trace_path = str(case_dir / trace_name)
                    await context.tracing.stop(path=trace_path)

                return UIEvidencePack(
                    case_id=request.case_id,
                    screenshot_path=screenshot_path,
                    trace_path=trace_path,
                    console_logs=console_logs,
                    page_url=page.url,
                    page_title=await page.title(),
                    viewport_size={'width': 1280, 'height': 720}
                )

            except Exception as e:
                # Fallback for failures
                return UIEvidencePack(
                    case_id=request.case_id,
                    page_url=request.target_url,
                    page_title="Error",
                    viewport_size={'width': 1280, 'height': 720},
                    metadata={"error": str(e)}
                )
            finally:
                await browser.close()

    def get_mock_evidence(self, case_id: str) -> UIEvidencePack:
        """
        Testler veya hızlı prototipleme için sahte kanıt paketi döner.
        """
        return UIEvidencePack(
            case_id=case_id,
            screenshot_path=f"repair_outputs/{case_id}/evidence/mock_screenshot.png",
            trace_path=f"repair_outputs/{case_id}/evidence/mock_trace.zip",
            console_logs=[
                UIConsoleLog(level="error", message="Failed to load resource: the server responded with a status of 404", timestamp=datetime.now(timezone.utc)),
                UIConsoleLog(level="warning", message="Slow network detected", timestamp=datetime.now(timezone.utc))
            ],
            page_url="https://app.sovereign-agi.local/dashboard",
            page_title="Sovereign Control Plane",
            viewport_size={'width': 1280, 'height': 720},
            metadata={"mode": "SIMULATED"}
        )
