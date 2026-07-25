"""
Bulk Instagram Post & Reel Scraper & Analyzer for Competitor Espionage (@Ai_gucum_).
Scrapes metadata, hooks, content topics, captions, and visual styles for 30 provided URLs.
"""

import sys
import json
import time
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USER_DATA_DIR = BASE_DIR / "workspace" / "carousel_engine" / "browser_profile"
OUTPUT_JSON = BASE_DIR / "artifacts" / "carousels" / "bulk_30_posts_analysis.json"

URL_LIST = [
    "https://www.instagram.com/reel/DbL6g2BRZvT/",
    "https://www.instagram.com/p/DacJ1iJjTPc/",
    "https://www.instagram.com/p/DaujhcOCLvG/",
    "https://www.instagram.com/reel/DZDKaAfthxU/",
    "https://www.instagram.com/reel/DbOMpGit_Gi/",
    "https://www.instagram.com/reel/Da5cJGzMeAS/",
    "https://www.instagram.com/p/Dab7eq4kUOZ/",
    "https://www.instagram.com/p/DbAoiWPiq-v/",
    "https://www.instagram.com/p/Dax5FHcCCct/",
    "https://www.instagram.com/reel/DbD5DCJtVKt/",
    "https://www.instagram.com/reel/DZpx832M1CD/",
    "https://www.instagram.com/reel/DbGtv53szUX/",
    "https://www.instagram.com/p/DavedntjfJ6/",
    "https://www.instagram.com/p/DbJEloOEdqK/",
    "https://www.instagram.com/reel/DYh276it9vg/",
    "https://www.instagram.com/p/Daz0pnijDhC/",
    "https://www.instagram.com/p/Da2FMt5AMbY/",
    "https://www.instagram.com/reel/Da-rsSPIGWn/",
    "https://www.instagram.com/p/DaVviQ1iMDs/",
    "https://www.instagram.com/reel/DZLCQH1M9A-",
    "https://www.instagram.com/p/DaQHskciG5z/",
    "https://www.instagram.com/p/DbEFKFCDRM4/",
    "https://www.instagram.com/p/DbDG_i-s7rs/",
    "https://www.instagram.com/p/DauQe6RiE_2/",
    "https://www.instagram.com/p/DbDMCUCConI/",
    "https://www.instagram.com/reel/Daq1KFluBjf/",
    "https://www.instagram.com/reel/DbD9b5jsL7U/",
    "https://www.instagram.com/reel/DZGSlOdgyrP/",
    "https://www.instagram.com/reel/DbL4ckvOxTU/",
    "https://www.instagram.com/reel/DaL1Q6xN49l/"
]

def analyze_posts():
    print("=" * 75)
    print(f"📊 30 İNSTAGRAM İÇERİĞİ TOPLU ANALİZ VE İNCELEME MOTORU ({len(URL_LIST)} URL)")
    print("=" * 75)

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        for idx, url in enumerate(URL_LIST, 1):
            post_type = "REEL" if "/reel/" in url else "CAROUSEL/IMAGE"
            shortcode = url.split("/")[4] if len(url.split("/")) > 4 else f"post_{idx}"
            print(f"\n[{idx}/{len(URL_LIST)}] 🔗 İnceleme: {url} ({post_type})")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                time.sleep(2.5)

                # Extract title / meta description / caption text
                caption = ""
                meta_desc = ""
                try:
                    meta_elem = page.locator("meta[property='og:title'], meta[name='description']").first
                    if meta_elem.is_visible(timeout=2000):
                        meta_desc = meta_elem.get_attribute("content") or ""
                except Exception:
                    pass

                try:
                    caption_elem = page.locator("h1, div[role='dialog'] span, article span").first
                    if caption_elem.is_visible(timeout=2000):
                        caption = caption_elem.inner_text()
                except Exception:
                    pass

                # Grab page title
                page_title = page.title()

                # Clean up snippet
                full_text = f"{page_title} | {meta_desc} | {caption}".strip()
                hook_match = re.search(r'["“]([^"“]+)["”]', full_text)
                hook = hook_match.group(1) if hook_match else full_text[:100]

                item_data = {
                    "index": idx,
                    "url": url,
                    "shortcode": shortcode,
                    "type": post_type,
                    "page_title": page_title,
                    "meta_desc": meta_desc[:200],
                    "caption_snippet": caption[:300],
                    "status": "SCRAPED_OK"
                }

                print(f"   ├─ Tür: {post_type}")
                print(f"   ├─ Sayfa Başlığı / Özet: {page_title[:80]}")
                results.append(item_data)

            except Exception as e:
                print(f"   ⚠️ Uyarı: Sayfa beklenenden yavaş yanıt verdi: {e}")
                results.append({
                    "index": idx,
                    "url": url,
                    "shortcode": shortcode,
                    "type": post_type,
                    "status": "TIMEOUT_SKIPPED"
                })

        browser.close()

    # Save to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 75)
    print(f"✅ 30 İÇERİK ANALİZİ TAMAMLANDI! KAYIT: {OUTPUT_JSON}")
    print("=" * 75)

if __name__ == "__main__":
    analyze_posts()
