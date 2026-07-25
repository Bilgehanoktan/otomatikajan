"""
Autonomous Interactive Instagram Story Generator & Scheduler Engine for @Ai_gucum_.
Generates 3 daily 1080x1920 9:16 vertical Story slides:
1. Poll Story (DeepSeek vs ChatGPT)
2. Quiz Story (AI Code Challenge)
3. Link Sticker Story (Free AI Prompt Vault)
"""

import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORY_DIR = BASE_DIR / "artifacts" / "carousels" / "story_packages"

STORY_TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>Instagram Story Template</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@800;900&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      width: 1080px; height: 1920px; background: #050811; color: #ffffff;
      font-family: 'Plus Jakarta Sans', sans-serif; overflow: hidden; position: relative;
      display: flex; flex-direction: column; justify-content: space-between; padding: 100px 70px 90px 70px;
    }
    .orb { position: absolute; border-radius: 50%; filter: blur(150px); opacity: 0.8; z-index: 0; }
    .orb-cyan { width: 900px; height: 900px; background: rgba(0, 242, 254, 0.26); top: -200px; left: -200px; }
    .orb-purple { width: 900px; height: 900px; background: rgba(157, 78, 221, 0.24); bottom: -200px; right: -200px; }
    
    .card {
      position: relative; z-index: 10; width: 100%; height: 100%;
      background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(40px);
      border: 2px solid rgba(0, 242, 254, 0.4); border-radius: 44px;
      padding: 70px 60px; display: flex; flex-direction: column; justify-content: space-between;
      box-shadow: 0 40px 100px rgba(0,0,0,0.9);
    }
    .tag {
      background: #00f2fe; color: #050811; font-size: 22px; font-weight: 900;
      letter-spacing: 1.5px; padding: 10px 26px; border-radius: 999px; display: inline-block;
      text-transform: uppercase;
    }
    .title {
      font-family: 'Outfit', sans-serif; font-size: 56px; font-weight: 900; line-height: 1.15;
      margin-top: 30px; margin-bottom: 24px;
    }
    .interactive-box {
      background: rgba(30, 41, 59, 0.7); border: 2px solid rgba(255,255,255,0.15);
      border-radius: 32px; padding: 44px; display: flex; flex-direction: column; gap: 20px;
    }
    .opt {
      background: rgba(0, 242, 254, 0.15); border: 1.5px solid rgba(0, 242, 254, 0.5);
      border-radius: 20px; padding: 24px 30px; font-size: 28px; font-weight: 800; color: #ffffff;
      display: flex; justify-content: space-between; align-items: center;
    }
    .footer {
      font-size: 24px; font-weight: 800; color: #00f2fe; text-align: center;
    }
  </style>
</head>
<body>
  <div class="orb orb-cyan"></div>
  <div class="orb orb-purple"></div>
  <div class="card">
    <div>
      <div class="tag">{{STORY_TAG}}</div>
      <h1 class="title">{{STORY_TITLE}}</h1>
    </div>
    <div class="interactive-box">
      <div class="opt"><span>A) {{OPT_A}}</span> <span>🔥</span></div>
      <div class="opt" style="background: rgba(157,78,221,0.15); border-color: rgba(157,78,221,0.5);"><span>B) {{OPT_B}}</span> <span>🚀</span></div>
    </div>
    <div class="footer">⚡ @Ai_gucum_ • Günlük AI Hikaye Anketi</div>
  </div>
</body>
</html>
"""

def generate_daily_stories() -> List[Path]:
    print("=" * 70)
    print("📱 ADIM 3: GÜNLÜK HİKAYE (STORY) VE ETKİLEŞİM MOTORU (@Ai_gucum_)")
    print("=" * 70)

    STORY_DIR.mkdir(parents=True, exist_ok=True)

    stories_config = [
        {"num": 1, "tag": "📊 GÜNÜN ANKETİ", "title": "Sizce Hangisi Daha Güçlü Kod Yazar?", "opt_a": "DeepSeek R1", "opt_b": "ChatGPT o1"},
        {"num": 2, "tag": "💡 YAPAY ZEKA TESTİ", "title": "Tek Komutla Web Sitesi Üreten Araç Hangisi?", "opt_a": "Bolt.new", "opt_b": "Canva"},
        {"num": 3, "tag": "🔗 ÜCRETSİZ REHBER", "title": "50+ Kopyalanabilir AI Promptunu Hemen Al", "opt_a": "Notion Kütüphanesi", "opt_b": "PDF Dosyası"}
    ]

    generated_paths = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for s in stories_config:
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            html = STORY_TEMPLATE_HTML.replace("{{STORY_TAG}}", s["tag"])\
                                      .replace("{{STORY_TITLE}}", s["title"])\
                                      .replace("{{OPT_A}}", s["opt_a"])\
                                      .replace("{{OPT_B}}", s["opt_b"])
            out_file = STORY_DIR / f"story_{s['num']}_hd.png"
            page.set_content(html, wait_until="networkidle")
            page.screenshot(path=str(out_file))
            generated_paths.append(out_file)
            print(f"   ✅ Hikaye {s['num']} Üretildi: {out_file.name}")
        browser.close()

    print(f"🎉 Toplam {len(generated_paths)} Adet Günlük Hikaye Başarıyla Oluşturuldu!")
    return generated_paths

if __name__ == "__main__":
    generate_daily_stories()
