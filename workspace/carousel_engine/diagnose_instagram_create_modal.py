"""
Diagnostic script to inspect Instagram Web Create Modal UI elements and selectors.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USER_DATA_DIR = BASE_DIR / "workspace" / "carousel_engine" / "browser_profile"

def diagnose_create_modal():
    print("🔍 Instagram Create Modal Teşhis Motoru Başlatılıyor...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print("🔗 https://www.instagram.com/ açılıyor...")
        page.goto("https://www.instagram.com/", wait_until="networkidle")
        time.sleep(4)

        # Screenshot initial state
        page.screenshot(path=str(BASE_DIR / "artifacts" / "carousels" / "diag_1_home.png"))

        # Look for Create button
        create_selectors = [
            "svg[aria-label='Yeni Gönderi']",
            "svg[aria-label='New post']",
            "span:has-text('Oluştur')",
            "span:has-text('Create')",
            "a[href='#']:has(svg)"
        ]

        found = False
        for sel in create_selectors:
            loc = page.locator(sel).first
            if loc.is_visible():
                print(f"✅ Oluştur Butonu Bulundu: {sel}")
                loc.click()
                found = True
                break

        time.sleep(3)
        page.screenshot(path=str(BASE_DIR / "artifacts" / "carousels" / "diag_2_modal.png"))

        # Inspect all file inputs and buttons inside dialog
        inputs = page.locator("input[type='file']").all()
        print(f"📊 Bulunan <input type='file'> Sayısı: {len(inputs)}")

        buttons = page.locator("button").all()
        print(f"📊 Modal İçi Buton Sayısı: {len(buttons)}")
        for b in buttons[:15]:
            try:
                txt = b.inner_text()
                if txt.strip():
                    print(f"   ├─ Buton Metni: '{txt}'")
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    diagnose_create_modal()
