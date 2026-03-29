import asyncio
import base64
import os
from playwright.async_api import async_playwright
from observability.logging import get_logger

logger = get_logger("visual_util")

async def capture_screenshot(url: str = "http://localhost:8000") -> str:
    """
    Uygulamanın ekran görüntüsünü alır ve base64 string olarak döner.
    """
    logger.info(f"📸 Ekran görüntüsü yakalanıyor: {url}")
    async with async_playwright() as p:
        # Tarayıcıyı başlat (Chromium)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            device_scale_factor=2, # Yüksek çözünürlük için (Retina benzeri)
        )
        page = await context.new_page()
        
        try:
            # Sayfaya git
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # TODO: Gerekiyorsa burada login adımları eklenebilir.
            # Şimdilik sadece ana sayfayı alıyoruz.
            
            # CSS animasyonlarının oturması için kısa bir bekleme
            await asyncio.sleep(2)
            
            # Ekran görüntüsü al (buffer olarak)
            screenshot_bytes = await page.screenshot(full_page=False)
            
            # Base64'e çevir
            encoded = base64.b64encode(screenshot_bytes).decode('utf-8')
            logger.info("✅ Ekran görüntüsü başarıyla alındı.")
            return encoded
            
        except Exception as e:
            logger.error(f"❌ Ekran görüntüsü alma hatası: {e}")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    # Test amaçlı
    async def test():
        try:
            b64 = await capture_screenshot()
            print(f"Base64 length: {len(b64)}")
            with open("test_screenshot.txt", "w") as f:
                f.write(b64)
        except Exception as e:
            print(f"Test hatası: {e}")
            
    asyncio.run(test())
