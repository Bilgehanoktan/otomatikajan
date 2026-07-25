"""
Inspects live @Ai_gucum_ profile page and captures screenshot.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USER_DATA_DIR = BASE_DIR / "workspace" / "carousel_engine" / "browser_profile"

def inspect_profile():
    print("=" * 70)
    print("🔍 LIVE PROFILE INSPECTION: https://www.instagram.com/Ai_gucum_/")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.new_page()
        page.goto("https://www.instagram.com/Ai_gucum_/", wait_until="networkidle")
        time.sleep(4)

        # Screenshot profile
        profile_img = BASE_DIR / "artifacts" / "carousels" / "live_profile_check.png"
        page.screenshot(path=str(profile_img))
        print(f"📸 Live profile screenshot saved: {profile_img}")

        # Check post count text
        try:
            posts_count = page.locator("header section li").first.inner_text()
            print(f"📌 Profile stats: {posts_count}")
        except Exception as e:
            print(f"Note: {e}")

        browser.close()

if __name__ == "__main__":
    inspect_profile()
