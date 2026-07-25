"""
Diagnostic step to inspect the exact DOM after clicking 'Gönderi'.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USER_DATA_DIR = BASE_DIR / "workspace" / "carousel_engine" / "browser_profile"

def diagnose_after_gonderi():
    print("🔍 Instagram 'Gönderi' Tıklama Sonrası Teşhis Başlatılıyor...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        page.goto("https://www.instagram.com/", wait_until="networkidle")
        time.sleep(3)

        olustur_menu = page.locator("span:has-text('Oluştur'), svg[aria-label='Yeni Gönderi']").first
        if olustur_menu.is_visible():
            olustur_menu.click()
            time.sleep(2)

        gonderi_sub = page.locator("span:has-text('Gönderi')").first
        if gonderi_sub.is_visible():
            gonderi_sub.click()
            time.sleep(3)

        shot_path = BASE_DIR / "artifacts" / "carousels" / "diag_3_post_modal.png"
        page.screenshot(path=str(shot_path))
        print(f"📸 Screenshot Saklandı: {shot_path}")

        # Print all visible buttons and text on page
        print("📊 Açık Diyalogtaki Görünür Metinler:")
        texts = page.locator("div[role='dialog'] *").all_inner_texts()
        for t in texts:
            if t.strip() and len(t.strip()) < 50:
                print(f"   ├─ '{t.strip()}'")

        browser.close()

if __name__ == "__main__":
    diagnose_after_gonderi()
