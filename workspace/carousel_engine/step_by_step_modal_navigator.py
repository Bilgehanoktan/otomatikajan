"""
Step-by-step modal navigator to diagnose exact 'İleri' buttons and caption input box.
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

def navigate_modal():
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

        print("📸 2. Oluştur -> Gönderi...")
        page.locator("svg[aria-label='Yeni Gönderi'], span:has-text('Oluştur')").first.click()
        time.sleep(1.5)

        gonderi_item = page.locator("div[role='dialog'] span:has-text('Gönderi'), span:has-text('Gönderi')").last
        gonderi_item.click()
        time.sleep(3)

        print("📁 3. FileChooser ile dosyalar yükleniyor...")
        select_btn = page.locator("button:has-text('Bilgisayardan seç'), button:has-text('Select from computer')").first
        with page.expect_file_chooser(timeout=10000) as fc_info:
            select_btn.click()
        fc_info.value.set_files(files)
        time.sleep(4)

        # Screenshot 1: Crop Screen
        page.screenshot(path=str(BASE_DIR / "artifacts" / "carousels" / "nav_1_crop.png"))
        print("📸 Screenshot nav_1_crop.png saklandı.")

        # Click top-right 'İleri'
        print("➡️ 4. Kırp ekranında top-right 'İleri' tıklanıyor...")
        # Exact top-right header button selector
        header_ileri = page.locator("div[role='dialog'] header div[role='button']:has-text('İleri'), div[role='dialog'] header button:has-text('İleri'), div[role='dialog'] h1 ~ div:has-text('İleri')").first
        if not header_ileri.is_visible():
            header_ileri = page.locator("*:has-text('İleri')").all()[-1]
        
        print(f"   ├─ Tıklanacak İleri Metni: '{header_ileri.inner_text()}'")
        header_ileri.click()
        time.sleep(4)

        # Screenshot 2: Filter Screen
        page.screenshot(path=str(BASE_DIR / "artifacts" / "carousels" / "nav_2_filter.png"))
        print("📸 Screenshot nav_2_filter.png saklandı.")

        # Click top-right 'İleri' again for Caption screen
        print("➡️ 5. Filtre ekranında top-right 'İleri' tıklanıyor...")
        header_ileri_2 = page.locator("div[role='dialog'] header div[role='button']:has-text('İleri'), div[role='dialog'] header button:has-text('İleri')").first
        if header_ileri_2.is_visible():
            header_ileri_2.click()
            time.sleep(4)

        # Screenshot 3: Caption Screen
        page.screenshot(path=str(BASE_DIR / "artifacts" / "carousels" / "nav_3_caption.png"))
        print("📸 Screenshot nav_3_caption.png saklandı.")

        # Print all inputs/textareas/divs on dialog
        print("📊 Modal İçi Giriş Alanları:")
        editable_elements = page.locator("div[role='dialog'] [contenteditable='true'], div[role='dialog'] textarea, div[role='dialog'] div[aria-label]").all()
        for idx, elem in enumerate(editable_elements, 1):
            try:
                print(f"   ├─ [{idx}] Tag: {elem.evaluate('el => el.tagName')}, Aria-Label: '{elem.get_attribute('aria-label')}'")
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    navigate_modal()
