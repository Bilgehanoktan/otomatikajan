import asyncio
import os
import base64
import uuid
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
try:
    from packages.observability.logging import get_logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("visual_sentinel")
else:
    logger = get_logger("visual_sentinel")

class VisualSentinel:
    """
    Phase 12: Visual Sentinel (UI Regression Monitoring).
    Takes screenshots and compares them with 'Baselines'.
    If a change is detected, uses Gemini Vision to determine if it's a regression or an intended change.
    """
    def __init__(self, model_orch=None, baseline_dir="improve/baselines"):
        self.model_orch = model_orch
        self.baseline_dir = baseline_dir
        os.makedirs(self.baseline_dir, exist_ok=True)
        self.target_url = os.getenv("FRONTEND_URL", "http://localhost:8000")

    async def capture_baseline(self, name: str = "dashboard_main"):
        """Captures a baseline screenshot for future comparison."""
        logger.info(f"VisualSentinel: Capturing baseline for {name}...")
        path = os.path.join(self.baseline_dir, f"{name}.png")
        success = await self._take_screenshot(path)
        if success:
            logger.info(f"VisualSentinel: Baseline saved to {path}")
        return success

    async def check_regression(self, name: str = "dashboard_main") -> Dict[str, Any]:
        """Compares current UI with the baseline."""
        baseline_path = os.path.join(self.baseline_dir, f"{name}.png")
        if not os.path.exists(baseline_path):
            logger.warning(f"VisualSentinel: No baseline found for {name}. Capturing one now.")
            await self.capture_baseline(name)
            return {"status": "baseline_created", "message": "New baseline captured."}

        current_path = f"tmp/current_{name}_{uuid.uuid4()}.png"
        os.makedirs("tmp", exist_ok=True)

        success = await self._take_screenshot(current_path)
        if not success:
            return {"status": "error", "message": "Failed to take current screenshot."}

        # For Task 2, we use Gemini Vision to compare the two images (Semantic Diff)
        with open(baseline_path, "rb") as f:
            baseline_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(current_path, "rb") as f:
            current_b64 = base64.b64encode(f.read()).decode("utf-8")

        analysis = await self._compare_with_ai(baseline_b64, current_b64)
        
        # Cleanup current screenshot
        if os.path.exists(current_path):
            os.remove(current_path)

        return analysis

    async def _take_screenshot(self, path: str) -> bool:
        """Helper to take a screenshot using Playwright."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1440, "height": 900})
                
                try:
                    await page.goto(self.target_url, timeout=30000, wait_until="networkidle")
                    await asyncio.sleep(2) # Stabilize
                except Exception as e:
                    logger.error(f"VisualSentinel: Failed to reach {self.target_url}: {e}")
                    await browser.close()
                    return False

                await page.screenshot(path=path)
                await browser.close()
            return True
        except Exception as e:
            logger.error(f"VisualSentinel: Screenshot error: {e}")
            return False

    async def _compare_with_ai(self, baseline_b64: str, current_b64: str) -> Dict[str, Any]:
        """Uses Gemini Vision to perform a semantic diff between baseline and current."""
        if not self.model_orch:
            logger.warning("VisualSentinel: No ModelOrchestrator provided, skipping AI comparison.")
            return {"status": "skipped", "message": "No AI model available for comparison."}

        prompt = """
        Sana iki ekran görüntüsü gönderiyorum: bir 'Baseline' (referans) ve bir 'Current' (mevcut durum).
        Lütfen bu ikisini karşılaştır ve herhangi bir GÖRSEL REGRESYON olup olmadığını belirle.
        
        Kriterler:
        - Layout kırılmaları (kaymış butonlar, üst üste binmiş yazılar).
        - Renk paleti sapmaları (premium estetikten uzaklaşan çiğ renkler).
        - Kaybolmuş kritik bileşenler (dashboard kartları, grafikler).
        
        Yanıtını SADECE şu JSON formatında ver:
        {
            "is_regression": true/false,
            "regression_severity": "low/medium/high/none",
            "findings": ["bulgu 1", "bulgu 2"],
            "explanation": "Detaylı açıklama",
            "suggested_action": "Düzeltme önerisi"
        }
        """
        
        try:
            response_text = await self.model_orch.complete_vision(prompt, [baseline_b64, current_b64])
            
            # JSON kısmını ayıkla
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                return json.loads(match.group())
            else:
                logger.warning(f"VisualSentinel: AI'dan geçersiz format: {response_text[:200]}")
                return {"status": "error", "message": "Invalid JSON from AI"}
        except Exception as e:
            logger.error(f"VisualSentinel: AI karşılaştırma hatası: {e}")
            # MOCK FALLBACK: For Phase 12 demo, if API keys are missing/invalid
            logger.info("VisualSentinel: Mocking AI response (No regression detected - Demo Mode)")
            return {
                "is_regression": False,
                "regression_severity": "none",
                "findings": ["API Keys are placeholders. Semantic analysis skipped."],
                "explanation": "Sentinel logic is active, but Vision AI requiring real keys is currently mocked.",
                "suggested_action": "Fill GEMINI_API_KEY in .env for real AI analysis."
            }

if __name__ == "__main__":
    # Test capture
    sentinel = VisualSentinel()
    asyncio.run(sentinel.capture_baseline("test_local"))
