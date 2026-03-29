import asyncio
import os
import base64
import uuid
import json
import re
import httpx
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from db.models import ImprovementOpportunity
from observability.logging import get_logger

logger = get_logger("visual_observer")

class VisualUXObserver:
    """
    Sistemin frontend arayüzünü görsel olarak inceleyen ve iyileştirme önerileri sunan gözlemci.
    Faz 12: Playwright + Gemini Vision entegrasyonu.
    """

    def __init__(self, db_session, model_orch):
        self.db = db_session
        self.model_orch = model_orch
        # Docker ortamında 'app' servisine, localde 'localhost'a bakar.
        self.target_url = os.getenv("FRONTEND_URL", "http://localhost:8000")

    async def scan(self) -> List[Dict[str, Any]]:
        """
        Dashboard'ın ekran görüntüsünü alır ve UX/UI analizi yapar.
        CEOEngine tarafından işlenebilecek bir liste döner.
        """
        logger.info(f"VisualUXObserver: {self.target_url} için görsel tarama başlatılıyor...")
        
        screenshot_path = f"tmp/screenshot_{uuid.uuid4()}.png"
        os.makedirs("tmp", exist_ok=True)

        try:
            async with async_playwright() as p:
                # Browser başlat
                try:
                    browser = await p.chromium.launch(headless=True)
                except Exception as b_err:
                    logger.error(f"VisualUXObserver: Browser başlatılamadı. Playwright bağımlılıkları eksik olabilir: {b_err}")
                    # Faz 12.1: 'Visual Blindness' durumunu raporla
                    return [{
                        "source_type": "visual_audit",
                        "title": "Sistem Görsel Körlük (Visual Blindness)",
                        "description": "Playwright/Chromium bağımlılıkları eksik olduğu için arayüz denetimi yapılamıyor.",
                        "severity": "medium",
                        "category": "infrastructure_gap",
                        "evidence_detail": json.dumps({"error": str(b_err)})
                    }]
                    
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1440, "height": 900})
                
                try:
                    logger.debug(f"VisualUXObserver: URL'e gidiliyor: {self.target_url}")
                    await page.goto(self.target_url, timeout=20000, wait_until="networkidle")
                    # Dinamik içeriklerin yüklenmesi için kısa bir bekleme
                    await asyncio.sleep(3) 
                except Exception as e:
                    logger.error(f"VisualUXObserver: Hedef URL'e ulaşılamadı ({self.target_url}): {e}")
                    await browser.close()
                    return []

                await page.screenshot(path=screenshot_path, full_page=False)
                await browser.close()
            
            if not os.path.exists(screenshot_path):
                logger.warning("VisualUXObserver: Ekran görüntüsü oluşturulamadı.")
                return []

            logger.info("VisualUXObserver: Ekran görüntüsü alındı, analiz ediliyor...")
            
            with open(screenshot_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            
            # GPT-4o veya Gemini Vision ile analiz et
            analysis = await self._analyze_screenshot(img_data)
            
            # Temizlik
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            # CEOEngine formatına dönüştür
            opportunities = []
            for item in analysis:
                opportunities.append({
                    "source_type": "visual_audit",
                    "source_ref": f"ui_scan_{datetime.now().strftime('%Y%m%d_%H')}",
                    "title": item.get("title", "Arayüz Geliştirmesi"),
                    "description": item.get("description", ""),
                    "severity": item.get("severity", "medium"),
                    "category": "ux_design",
                    "evidence_detail": json.dumps({
                        "suggested_fix": item.get("suggest_fix", ""),
                        "potential_impact": item.get("potential_impact", ""),
                        "audit_type": "vision_ai"
                    }, ensure_ascii=False)
                })
            
            logger.info(f"VisualUXObserver: {len(opportunities)} görsel iyileştirme fırsatı bulundu.")
            return opportunities

        except Exception as e:
            logger.error(f"VisualUXObserver tarama hatası: {e}", exc_info=True)
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return []

    async def _analyze_screenshot(self, base64_image: str) -> List[Dict[str, Any]]:
        """Vision modelini kullanarak ekran görüntüsünü yorumlar."""
        prompt = """
        Sana sistemimizin dashboard ekran görüntüsünü gönderiyorum. 
        Bu dashboard, otonom bir AI yazılım şirketinin yönetim paneli. 
        Hedefimiz: 'Ultra-Modern', 'Premium', 'Dark-Mode' ve 'Developer-Friendly' bir estetik.
        
        Lütfen ekran görüntüsünü incele ve şu alanlarda iyileştirme öner:
        1. Görsel tutarsızlıklar (renk paleti uyumsuzluğu, hizalama hataları).
        2. UX darboğazları (anlaşılamayan grafikler, eksik durum bildirimleri).
        3. Estetik dokunuşlar (Glassmorphism, neon vurgular, daha iyi gradient geçişleri, micro-animation önerileri).
        4. Okunabilirlik ve erişilebilirlik.

        NOT (Opsiyonel Derinleştirme): Eğer bir bileşen (component) çok karmaşıksa veya sadece ekran görüntüsünden 
        tam anlaşılamıyorsa, CEO'ya 'browser_investigator' (MCP tabanlı uzman ajan) ile derinlemesine 
        DOM incelemesi yapılmasını önerin.
        
        Yanıtını SADECE şu formatta bir JSON listesi olarak ver:
        [
          {
            "title": "Kısa başlık",
            "description": "Bulgu özeti",
            "severity": "low|medium|high",
            "suggest_fix": "Yazılımcıya spesifik CSS/HTML talimatı veya 'browser_investigator' ile derin inceleme önerisi",
            "potential_impact": "Kullanıcı deneyimine etkisi"
          }
        ]
        """
        
        try:
            # ModelOrchestrator'daki yeni complete_vision metodunu kullan
            response_text = await self.model_orch.complete_vision(prompt, base64_image)
            
            # JSON kısmını ayıkla
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if match:
                return json.loads(match.group())
            else:
                logger.warning(f"VisualUXObserver: Vision modelinden geçersiz format: {response_text[:200]}")
        except Exception as e:
            logger.error(f"VisualUXObserver: AI analizi sırasında hata: {e}")
        
        return []
