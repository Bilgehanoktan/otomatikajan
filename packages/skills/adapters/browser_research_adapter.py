import asyncio
import os
from typing import Any, List

from packages.skills.base import BaseSkillAdapter, SkillRequest, SkillResult


class BrowserResearchSkillAdapter(BaseSkillAdapter):
    skill_id = "browser_research"

    def can_handle(self, req: SkillRequest) -> bool:
        text = f"{req.title} {req.description}".lower()
        return any(k in text for k in ["arastir", "research", "browse", "go to", "search documentation", "dokuman oku"])

    async def execute(self, req: SkillRequest) -> SkillResult:
        """
        GStack /browse mantigiyla cok adimli tarayici arastirmasi yapar.
        """
        try:
            from playwright.async_api import async_playwright

            query = req.context.get("query") or req.description
            max_steps = req.context.get("max_steps", 3)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # 1. Google ile basla
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                await page.goto(search_url, wait_until="networkidle")
                
                findings = []
                # Findings baslangici
                findings.append({"type": "info", "content": f"Search started for: {query}"})

                # İlk birkac linki bul
                links = await page.eval_on_selector_all("h3", "elements => elements.map(e => e.parentElement.href).filter(h => h && h.startsWith('http'))")
                
                # Sadece ilk 2 linki gez (vakit ve kaynak tasarrufu)
                for i, link in enumerate(links[:2]):
                    if i >= max_steps: break
                    try:
                        await page.goto(link, timeout=15000, wait_until="domcontentloaded")
                        title = await page.title()
                        # Sayfa iceriginden ilk 500 karakteri al
                        text_content = await page.evaluate("document.body.innerText")
                        findings.append({
                            "type": "result",
                            "url": link,
                            "title": title,
                            "snippet": text_content[:500].strip() + "..."
                        })
                    except Exception as e:
                        findings.append({"type": "error", "url": link, "content": str(e)})

                await browser.close()

                return SkillResult(
                    success=True,
                    skill_id=self.skill_id,
                    summary=f"Arastirma tamamlandi. {len(findings)-1} kaynak incelendi.",
                    data={"findings": findings}
                )

        except Exception as e:
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                summary=f"Arastirma Hatasi: {str(e)}"
            )
