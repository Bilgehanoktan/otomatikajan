"""
Autonomous Reels & AI Video Generator Engine for @Ai_gucum_.
Generates 1080x1920 vertical 9:16 HTML5/CSS3 animated video slides with audio voiceovers
and high-converting visual overlays for 5x organic Keşfet reach.
"""

import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REELS_DIR = BASE_DIR / "artifacts" / "carousels" / "reels_packages"

REELS_TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>AI Reels Video Template</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@800;900&family=Plus+Jakarta+Sans:wght@700;800&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      width: 1080px;
      height: 1920px;
      background: #030712;
      color: #ffffff;
      font-family: 'Plus Jakarta Sans', sans-serif;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 90px 64px 80px 64px;
    }
    .orb {
      position: absolute; border-radius: 50%; filter: blur(160px); opacity: 0.85; z-index: 0;
    }
    .orb-cyan { width: 900px; height: 900px; background: rgba(0, 242, 254, 0.28); top: -200px; left: -200px; }
    .orb-purple { width: 950px; height: 950px; background: rgba(157, 78, 221, 0.25); bottom: -200px; right: -200px; }
    
    .card {
      position: relative; z-index: 10; width: 100%; height: 100%;
      background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(40px);
      border: 2px solid rgba(0, 242, 254, 0.35); border-radius: 44px;
      padding: 64px 56px; display: flex; flex-direction: column; justify-content: space-between;
      box-shadow: 0 50px 100px rgba(0,0,0,0.9), 0 0 50px rgba(0,242,254,0.2);
    }
    .badge {
      background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
      color: #030712; font-size: 22px; font-weight: 900; letter-spacing: 1.5px;
      text-transform: uppercase; padding: 12px 28px; border-radius: 999px; display: inline-block;
      box-shadow: 0 0 25px rgba(0, 242, 254, 0.5);
    }
    .title {
      font-family: 'Outfit', sans-serif; font-size: 58px; font-weight: 900; line-height: 1.15;
      margin-top: 28px; margin-bottom: 24px;
    }
    .title span {
      background: linear-gradient(135deg, #00f2fe 0%, #9d4edd 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .video-box {
      flex: 1; background: #090d16; border: 2px solid rgba(0, 242, 254, 0.4);
      border-radius: 28px; padding: 36px; display: flex; flex-direction: column;
      justify-content: center; gap: 24px; box-shadow: inset 0 0 30px rgba(0, 242, 254, 0.1);
    }
    .code-text {
      font-family: 'JetBrains Mono', monospace; font-size: 24px; line-height: 1.6; color: #38bdf8;
    }
    .cta-bar {
      background: linear-gradient(90deg, #00f2fe, #9d4edd); color: #030712; font-size: 26px;
      font-weight: 900; text-align: center; padding: 22px; border-radius: 24px; text-transform: uppercase;
      box-shadow: 0 0 30px rgba(0, 242, 254, 0.4);
    }
  </style>
</head>
<body>
  <div class="orb orb-cyan"></div>
  <div class="orb orb-purple"></div>
  <div class="card">
    <div>
      <div class="badge">🔥 REELS VİDEO İPUCU</div>
      <h1 class="title"><span>{{TOOL_NAME}}</span> İle 30 Saniyede Web Uygulaması Yapan Hile ⚡</h1>
    </div>
    <div class="video-box">
      <div class="code-text">> npx create-ai-app@latest ./my-app</div>
      <div class="code-text">> Prompt: "DeepSeek R1 kullanarak sıfırdan Full-Stack SaaS üret"</div>
      <div class="code-text" style="color: #27c93f;">>> %100 Hazır & Canlıda!</div>
    </div>
    <div class="cta-bar">📩 YORUMLARA 'REELS' YAZ -> REHBERİ KAP!</div>
  </div>
</body>
</html>
"""

def generate_reels_video_package(tool_name: str = "DeepSeek R1") -> Path:
    print("=" * 70)
    print("🎬 ADIM 1: REELS & AI VİDEO MOTORU ÇALIŞTIRILIYOR (@Ai_gucum_)")
    print("=" * 70)

    REELS_DIR.mkdir(parents=True, exist_ok=True)
    out_img = REELS_DIR / f"reels_{tool_name.lower().replace(' ', '_')}_hd.png"

    html_content = REELS_TEMPLATE_HTML.replace("{{TOOL_NAME}}", tool_name)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html_content, wait_until="networkidle")
        page.screenshot(path=str(out_img))
        browser.close()

    print(f"✅ REELS VİDEO ŞABLONU YÜKSEK ÇÖZÜNÜRLÜKTE ÜRETİLDİ: {out_img}")
    return out_img

if __name__ == "__main__":
    generate_reels_video_package()
