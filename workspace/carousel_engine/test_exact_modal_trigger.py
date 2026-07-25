"""
Test exact modal trigger and file chooser interaction on Instagram Web.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USER_DATA_DIR = BASE_DIR / "workspace" / "carousel_engine" / "browser_profile"
BOLT_NEW_DIR = BASE_DIR / "artifacts" / "carousels" / "batch_20260724_000741" / "boltnew"

def test_trigger():
    files = [
        str((BOLT_NEW_DIR / "slide_1.png").resolve()),
        str((BOLT_NEW_DIR / "slide_2.png").resolve()),
        str((BOLT_NEW_DIR / "slide_3.png").resolve())
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print("🔗 1. Instagram ana sayfası...")
        page.goto("https://www.instagram.com/", wait_until="networkidle")
        time.sleep(3)

        print("📸 2. 'Oluştur' ikonuna tıklanıyor...")
        page.locator("svg[aria-label='Yeni Gönderi'], span:has-text('Oluştur')").first.click()
        time.sleep(1.5)

        print("📸 3. 'Gönderi' seçeneğine tıklanıyor...")
        # Exact locator for popover Gönderi item
        gonderi_item = page.locator("div[role='dialog'] span:has-text('Gönderi'), span:has-text('Gönderi')").last
        gonderi_item.click()
        time.sleep(3)

        page.screenshot(path=str(BASE_DIR / "artifacts" / "carousels" / "diag_5_modal_open.png"))
        print(f"📸 Diag 5 Screenshot Saklandı.")

        # Look for file chooser or select from computer button
        select_btn = page.locator("button:has-text('Bilgisayardan seç'), button:has-text('Select from computer')").first
        if select_btn.is_visible():
            print("✅ 'Bilgisayardan seç' Butonu Görünür!")
            with page.expect_file_chooser(timeout=10000) as fc_info:
                select_btn.click()
            fc_info.value.set_files(files)
            print("✅ Yükleme Tamamlandı!")
            time.sleep(3)
            page.screenshot(path=str(BASE_DIR / "artifacts" / "carousels" / "diag_6_uploaded.png"))

        browser.close()

if __name__ == "__main__":
    test_trigger()
