import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def run():
    print("Testing Playwright local installation...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            print("Successfully launched Chromium.")
            page = await browser.new_page()
            await page.goto("https://www.google.com", timeout=30000)
            title = await page.title()
            print(f"Page Title: {title}")
            await browser.close()
            print("Playwright is operational on this host.")
        except Exception as e:
            print(f"Playwright test failed: {e}")
            print("Installing chromium if missing...")
            import subprocess
            subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)
            # Retry
            async with async_playwright() as p2:
                browser2 = await p2.chromium.launch(headless=True)
                print("Successfully launched Chromium after install.")
                await browser2.close()

if __name__ == "__main__":
    asyncio.run(run())
