"""
Live Real Publisher for @Ai_gucum_ with modal wait and real URL extraction.
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

def publish_live_and_get_real_url():
    print("=" * 75)
    print("🚀 REAL-TIME CANLI INSTAGRAM YAYINLAMA VE URL TESPİT MOTORU (@Ai_gucum_)")
    print("=" * 75)

    files = [
        str((BOLT_NEW_DIR / "slide_1.png").resolve()),
        str((BOLT_NEW_DIR / "slide_2.png").resolve()),
        str((BOLT_NEW_DIR / "slide_3.png").resolve())
    ]

    for f in files:
        if not Path(f).exists():
            raise FileNotFoundError(f"Görsel bulunamadı: {f}")

    print(f"✅ {len(files)} adet Ultra HD slide görseli doğrulandı.")

    caption = """⚡ Tek Komutla Full-Stack Web Sitesi Üreten Yapay Zeka Devrimi: Bolt.new!

📌 Neden önemli?
1. Tarayıcı içinde tam Node.js (WebContainer) ortamı çalıştırır.
2. Next.js 15, TailwindCSS ve Stripe entegrasyonlu kodu saniyeler içinde yazar.
3. Vercel & Netlify bağlantısı ile 30 saniyede canlıya alır.

👉 Yorumlara 'BOLT' yaz, ücretsiz canlı demo rehberini kap! #yapayzeka #boltnew #aigucum #nextjs"""

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print("🔗 1. Instagram ana sayfası açılıyor...")
        page.goto("https://www.instagram.com/", wait_until="networkidle")
        time.sleep(3)

        # Check login
        if page.locator("input[name='username']").is_visible(timeout=2000):
            print("⚠️ Oturum açılıyor...")
            page.fill("input[name='username']", "Ai_gucum_")
            page.fill("input[name='password']", "Bilgehanai33")
            page.click("button[type='submit']")
            time.sleep(5)

        print("📸 2. 'Oluştur' menüsüne tıklanıyor...")
        olustur_btn = page.locator("svg[aria-label='Yeni Gönderi'], span:has-text('Oluştur')").first
        olustur_btn.click()
        time.sleep(1.5)

        print("📸 3. 'Gönderi' seçeneğine tıklanıyor...")
        gonderi_item = page.locator("div[role='dialog'] span:has-text('Gönderi'), span:has-text('Gönderi')").last
        gonderi_item.click()
        time.sleep(3)

        print("📁 4. 'Bilgisayardan seç' butonuna basılıp görseller yükleniyor...")
        select_btn = page.locator("button:has-text('Bilgisayardan seç'), button:has-text('Select from computer')").first
        select_btn.wait_for(state="visible", timeout=10000)

        with page.expect_file_chooser(timeout=10000) as fc_info:
            select_btn.click()

        fc_info.value.set_files(files)
        print("   ✅ Görseller yüklendi!")
        time.sleep(4)

        print("➡️ 5. Kırp ekranında 'İleri' butonuna tıklanıyor...")
        ileri_1 = page.locator("div[role='dialog'] div[role='button']:has-text('İleri'), div[role='dialog'] button:has-text('İleri')").last
        ileri_1.click()
        time.sleep(3)

        print("➡️ 6. Filtre ekranında 'İleri' butonuna tıklanıyor...")
        ileri_2 = page.locator("div[role='dialog'] div[role='button']:has-text('İleri'), div[role='dialog'] button:has-text('İleri')").last
        ileri_2.click()
        time.sleep(3)

        print("📝 7. Caption metni giriliyor...")
        caption_box = page.locator("div[aria-label='Bir açıklama yaz...'], div[aria-label='Write a caption...'], div[contenteditable='true']").first
        caption_box.wait_for(state="visible", timeout=10000)
        caption_box.click()
        caption_box.fill(caption)
        time.sleep(2)

        print("🚀 8. 'Paylaş' butonuna tıklanıyor...")
        paylas_btn = page.locator("div[role='dialog'] div[role='button']:has-text('Paylaş'), div[role='dialog'] button:has-text('Paylaş')").last
        paylas_btn.click()

        print("⏳ 9. Gönderinin Instagram sunucularında işlenmesi bekleniyor (15 saniye)...")
        time.sleep(15)

        print("📸 10. Profil sayfasına gidilip en son canlı gönderi linki çekiliyor...")
        page.goto("https://www.instagram.com/Ai_gucum_/", wait_until="networkidle")
        time.sleep(5)

        shot_path = BASE_DIR / "artifacts" / "carousels" / "live_profile_feed_verified.png"
        page.screenshot(path=str(shot_path))
        print(f"📸 Profil Akışı Ekran Görüntüsü: {shot_path}")

        # Click top-left latest post link
        latest_link = page.locator("a[href*='/p/']").first
        if latest_link.is_visible(timeout=5000):
            href = latest_link.get_attribute("href")
            real_url = f"https://www.instagram.com{href}" if href.startswith("/") else href
            print(f"\n=======================================================================")
            print(f"🎉 CANLI GÖNDERİ GERÇEK URL: {real_url}")
            print(f"=======================================================================")
            latest_link.click()
            time.sleep(4)
            post_shot = BASE_DIR / "artifacts" / "carousels" / "live_post_modal_verified.png"
            page.screenshot(path=str(post_shot))
            print(f"📸 Gönderi Detay Ekran Görüntüsü: {post_shot}")
        else:
            print("⚠️ Profilde görünür gönderi bulunamadı.")

        browser.close()

if __name__ == "__main__":
    publish_live_and_get_real_url()
