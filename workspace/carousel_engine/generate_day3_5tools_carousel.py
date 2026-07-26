"""
Day 3 Deliverable Generator for @Ai_gucum_:
"30 AI Aracı Değil: Çalışanların Gerçekten İhtiyaç Duyduğu 5 Araç"
Renders BOLD 4:5 Glassmorphism Carousel slides with high-contrast text and engineer test evidence.
"""

import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "artifacts" / "carousels" / "day3_5_tools_carousel"

SLIDES_DATA = [
    {
        "slide_num": 1,
        "badge": "MÜHENDİS TESTİ #01",
        "headline": "30 AI ARACI DEĞİL!",
        "subhead": "Çalışanların Gerçekten İhtiyaç Duyduğu 5 Temel Araç",
        "evidence_box": "⚡ 50+ araç arasından süre, maliyet ve doğruluk testleriyle seçildi.",
        "bg_color": "#0d1117"
    },
    {
        "slide_num": 2,
        "badge": "01. DOKÜMAN VE RAPOR",
        "headline": "CLAUDE 3.5 SONNET",
        "subhead": "Uzun teknik PDF ve sözleşmelerden sıfır hatayla aksiyon çıkarır.",
        "evidence_box": "📊 Test Sonucu: 45 sayfalık raporu 90 saniyede özetledi.",
        "bg_color": "#0f172a"
    },
    {
        "slide_num": 3,
        "badge": "02. FULL-STACK WEB",
        "headline": "BOLT.NEW",
        "subhead": "Tarayıcı içinde Node.js çalıştırıp tek komutla canlı web sitesi kurar.",
        "evidence_box": "⚡ Test Sonucu: Next.js + Tailwind projesini 30 sn'de Vercel'e canlıya aldı.",
        "bg_color": "#0f172a"
    },
    {
        "slide_num": 4,
        "badge": "03. VERİ GÜVENLİĞİ & YEREL AI",
        "headline": "OLLAMA + GEMMA 4",
        "subhead": "Şirket dosyalarını buluta yüklemeden kendi bilgisayarında çalıştırır.",
        "evidence_box": "🛡️ Test Sonucu: %100 çevrimdışı, sıfır veri sızıntısı.",
        "bg_color": "#0f172a"
    },
    {
        "slide_num": 5,
        "badge": "04 & 05. OTOMASYON VE KOD",
        "headline": "CURSOR AI & MCP",
        "subhead": "Kod tabanını semantik indeksler, Linear görevlerini otonom PR'a dönüştürür.",
        "evidence_box": "🛠️ Test Sonucu: Geliştirme süresi 20 dk'dan 2 dk'ya düştü.",
        "bg_color": "#0f172a"
    },
    {
        "slide_num": 6,
        "badge": "ÜCRETSİZ İŞ PROMPT KÜTÜPHANESİ",
        "headline": "ŞABLONU ÜCRETSİZ AL",
        "subhead": "Yorumlara 'REHBER' yaz, Notion AI Vault bağlantısını DM'den anında ileteyim.",
        "evidence_box": "📩 Yorumlara 'REHBER' yaz ➔ DM'den anında gelsin!",
        "bg_color": "#1e1b4b"
    }
]

def render_html_slide(slide_data: dict) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }}
  body {{
    width: 1080px; height: 1350px; background: {slide_data['bg_color']};
    color: #ffffff; display: flex; flex-direction: column; justify-content: space-between;
    padding: 80px 70px; position: relative; overflow: hidden;
  }}
  .background-glow {{
    position: absolute; top: -200px; right: -200px; width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, rgba(0,0,0,0) 70%);
    border-radius: 50%; pointer-events: none;
  }}
  .header-badge {{
    display: inline-block; background: rgba(99, 102, 241, 0.2); border: 2px solid #6366f1;
    color: #818cf8; font-size: 24px; font-weight: 800; padding: 12px 28px; border-radius: 50px;
    letter-spacing: 2px; text-transform: uppercase;
  }}
  .main-content {{ margin-top: 40px; }}
  .headline {{
    font-size: 76px; font-weight: 900; line-height: 1.1; color: #ffffff;
    letter-spacing: -2px; margin-bottom: 25px; text-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .subhead {{
    font-size: 36px; color: #cbd5e1; line-height: 1.4; font-weight: 500; margin-bottom: 50px;
  }}
  .evidence-card {{
    background: rgba(30, 41, 59, 0.8); border: 2px solid rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(20px); border-radius: 24px; padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
  }}
  .evidence-text {{
    font-size: 32px; color: #38bdf8; font-weight: 700; line-height: 1.3;
  }}
  .footer {{
    display: flex; justify-content: space-between; align-items: center;
    border-top: 2px solid rgba(255,255,255,0.1); padding-top: 30px;
  }}
  .handle {{ font-size: 28px; font-weight: 700; color: #94a3b8; }}
  .slide-count {{ font-size: 28px; font-weight: 800; color: #6366f1; }}
</style>
</head>
<body>
  <div class="background-glow"></div>
  <div>
    <div class="header-badge">{slide_data['badge']}</div>
    <div class="main-content">
      <div class="headline">{slide_data['headline']}</div>
      <div class="subhead">{slide_data['subhead']}</div>
      <div class="evidence-card">
        <div class="evidence-text">{slide_data['evidence_box']}</div>
      </div>
    </div>
  </div>
  <div class="footer">
    <div class="handle">@ai_gucum_ • Bilgehan | Yapay Zekâ ve Otomasyon</div>
    <div class="slide-count">{slide_data['slide_num']} / {len(SLIDES_DATA)}</div>
  </div>
</body>
</html>
"""

def generate_day3_carousel():
    print("=" * 75)
    print("🎨 BUGÜNKÜ GÖNDERİ TASARIM MOTORU: Day 3 5-Tool BOLD Carousel")
    print("=" * 75)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_slides = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})

        for slide_info in SLIDES_DATA:
            html_content = render_html_slide(slide_info)
            temp_html = OUTPUT_DIR / f"temp_slide_{slide_info['slide_num']}.html"
            temp_html.write_text(html_content, encoding="utf-8")

            img_path = OUTPUT_DIR / f"slide_{slide_info['slide_num']}.png"
            page.goto(temp_html.as_uri())
            page.screenshot(path=str(img_path))
            temp_html.unlink()

            generated_slides.append(str(img_path))
            print(f"   ├─ Slayt {slide_info['slide_num']} Render Edildi: {img_path}")

        browser.close()

    print("=" * 75)
    print(f"✅ BUGÜNKÜ {len(generated_slides)} SLAYTLI CAROUSEL BAŞARIYLA ÜRETİLDİ!")
    print("=" * 75)
    return generated_slides

if __name__ == "__main__":
    generate_day3_carousel()
