"""
Inspect exact button selectors and text in Instagram Create Dialog.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USER_DATA_DIR = BASE_DIR / "workspace" / "carousel_engine" / "browser_profile"

def inspect_dialog():
    print("🔍 Instagram Modal Elemanları İnceleme Motoru...")
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

        olustur_btn = page.locator("svg[aria-label='Yeni Gönderi'], span:has-text('Oluştur')").first
        olustur_btn.click()
        time.sleep(2)

        gonderi_btn = page.locator("span:has-text('Gönderi')").first
        gonderi_btn.click()
        time.sleep(3)

        # Capture screenshot right after clicking 'Gönderi'
        page.screenshot(path=str(BASE_DIR / "artifacts" / "carousels" / "diag_4_gonderi_click.png"))
        print(f"📸 Screenshot: artifacts/carousels/diag_4_gonderi_click.png")

        # Check all buttons on the page
        all_buttons = page.locator("button, label, a[role='button']").all()
        print(f"📊 Toplam Tıklanabilir Buton/Label Sayısı: {len(all_buttons)}")
        for b in all_buttons:
            try:
                if b.is_visible():
                    txt = b.inner_text().strip()
                    if txt:
                        print(f"   ├─ Görünür Buton/Label: '{txt}'")
            except Exception:
                pass

        # Check all inputs on page
        all_inputs = page.locator("input").all()
        print(f"📊 Toplam Input Sayısı: {len(all_inputs)}")
        for inp in all_inputs:
            try:
                t = inp.get_attribute("type")
                acc = inp.get_attribute("accept")
                print(f"   ├─ Input Type: '{t}', Accept: '{acc}'")
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    inspect_dialog()
