import asyncio
import os
from datetime import datetime
from typing import Any

from skills.base import BaseSkillAdapter, SkillRequest, SkillResult


class BrowserValidatorSkillAdapter(BaseSkillAdapter):
    skill_id = "browser_validator"

    def can_handle(self, req: SkillRequest) -> bool:
        text = f"{req.title} {req.description}".lower()
        return any(k in text for k in ["qa", "browser", "ui test", "verify-ui", "screenshot", "ekran görüntüsü"])

    async def execute(self, req: SkillRequest) -> SkillResult:
        """
        Playwright kullanarak bir URL'i ziyaret eder, ekran görüntüsü alır ve gerekirse element kontrolü yapar.
        """
        try:
            from playwright.async_api import async_playwright

            url = req.context.get("url") or req.description.strip()
            if not url.startswith("http"):
                # Güvenlik ve kolaylık: localhost varsayımı (eğer sadece port veya path varsa)
                if url.startswith("/") or url.isdigit():
                    base = os.getenv("APP_URL", "http://127.0.0.1:8000")
                    url = f"{base.rstrip('/')}/{url.lstrip('/')}"
                else:
                    return SkillResult(
                        success=False,
                        skill_id=self.skill_id,
                        summary=f"Geçersiz URL: {url}",
                    )

            selector = req.context.get("selector")
            wait_time = req.context.get("wait_time", 2000)

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(viewport={'width': 1280, 'height': 720})
                page = await context.new_page()

                try:
                    # Sayfaya git
                    response = await page.goto(url, wait_until="networkidle", timeout=30000)
                    if not response:
                         return SkillResult(success=False, skill_id=self.skill_id, summary=f"Bağlantı reddedildi: {url}")
                    
                    await asyncio.sleep(wait_time / 1000) # Ekstra bekleme

                    # Ekran görüntüsü al
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    snap_dir = os.path.join(os.getcwd(), "snapshots")
                    os.makedirs(snap_dir, exist_ok=True)
                    snap_path = os.path.join(snap_dir, f"qa_{timestamp}.png")
                    await page.screenshot(path=snap_path)

                    # Element kontrolü (varsa)
                    found = True
                    if selector:
                        try:
                            await page.wait_for_selector(selector, timeout=5000)
                        except Exception:
                            found = False

                    summary = f"QA Doğrulama Tamamlandı: {url}"
                    if selector:
                        summary += f" | Element '{selector}' {'BULUNDU' if found else 'BULUNAMADI'}"

                    return SkillResult(
                        success=found,
                        skill_id=self.skill_id,
                        summary=summary,
                        data={
                            "url": url,
                            "status_code": response.status,
                            "screenshot_path": snap_path,
                            "element_found": found,
                            "title": await page.title(),
                        },
                    )

                finally:
                    await browser.close()

        except Exception as e:
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                summary=f"QA Hatası: {str(e)}",
            )
