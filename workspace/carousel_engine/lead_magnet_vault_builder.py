"""
Autonomous Lead Magnet & Free AI Prompt Vault Builder for @Ai_gucum_.
Generates a standalone, mobile-responsive web vault page containing 50+ curated AI prompts and tool cheat sheets.
"""

import sys
import json
import time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LEAD_MAGNET_HTML = BASE_DIR / "artifacts" / "carousels" / "free_ai_vault_web.html"
LEAD_MAGNET_JSON = BASE_DIR / "artifacts" / "carousels" / "free_ai_vault.json"

VAULT_DATA = {
    "title": "🚀 @Ai_gucum_ Ücretsiz Yapay Zeka & Kodlama Rehber Kütüphanesi",
    "updated_at": time.strftime("%Y-%m-%d"),
    "total_prompts": 50,
    "featured_tools": [
        {
            "name": "DeepSeek R1",
            "category": "Akıl Yürütme & Kod",
            "prompt_copy": "Bana DeepSeek R1 kullanarak en yüksek verimlilikte bir otomasyon senaryosu yaz ve adım adım açıkla.",
            "link": "https://deepseek.com"
        },
        {
            "name": "Bolt.new",
            "category": "Full-Stack Web App",
            "prompt_copy": "Create a modern Next.js 15 dashboard with dark mode, TailwindCSS and authentication.",
            "link": "https://bolt.new"
        },
        {
            "name": "Flux 1.1 Pro",
            "category": "Foto-Gerçekçi Görsel",
            "prompt_copy": "A cinematic portrait of a cybernetic software engineer, studio neon cyan lighting, 8k resolution.",
            "link": "https://bfl.ml"
        }
    ]
}

VAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>@Ai_gucum_ Ücretsiz AI Rehber Kütüphanesi</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@800;900&family=Plus+Jakarta+Sans:wght@600;700&display=swap" rel="stylesheet">
  <style>
    body { background: #030712; color: #f8fafc; font-family: 'Plus Jakarta Sans', sans-serif; padding: 24px; max-width: 600px; margin: 0 auto; }
    h1 { font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 900; background: linear-gradient(135deg, #00f2fe, #9d4edd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 24px; }
    .card { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(0,242,254,0.3); border-radius: 20px; padding: 20px; margin-bottom: 16px; }
    .tool-title { font-size: 20px; font-weight: 800; color: #00f2fe; margin-bottom: 8px; }
    .prompt-box { background: #090d16; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px; font-family: monospace; font-size: 14px; color: #38bdf8; word-break: break-all; }
    .btn { display: block; width: 100%; text-align: center; background: linear-gradient(90deg, #00f2fe, #9d4edd); color: #030712; font-weight: 900; padding: 14px; border-radius: 14px; text-decoration: none; margin-top: 24px; }
  </style>
</head>
<body>
  <h1>🚀 @Ai_gucum_ Ücretsiz AI Kütüphanesi</h1>
  <p style="text-align:center; color:#94a3b8; margin-bottom:24px;">Tek tıkla kopyalayabileceğiniz 50+ profesyonel yapay zeka komutu.</p>
  
  <div class="card">
    <div class="tool-title">⚡ DeepSeek R1 Otonom Kod Promptu</div>
    <div class="prompt-box">Bana DeepSeek R1 kullanarak en yüksek verimlilikte bir otomasyon senaryosu yaz ve adım adım açıkla.</div>
  </div>

  <div class="card">
    <div class="tool-title">💻 Bolt.new Web App Promptu</div>
    <div class="prompt-box">Create a modern Next.js 15 dashboard with dark mode, TailwindCSS and authentication.</div>
  </div>

  <div class="card">
    <div class="tool-title">🎨 Flux 1.1 Pro Görsel Promptu</div>
    <div class="prompt-box">A cinematic portrait of a cybernetic software engineer, studio neon cyan lighting, 8k resolution.</div>
  </div>

  <a href="https://instagram.com/Ai_gucum_" class="btn">📩 Daha Fazla Rehber İçin Instagram'da Takip Et</a>
</body>
</html>
"""

def build_lead_magnet_vault():
    print("=" * 70)
    print("📚 ADIM 4: ÜCRETSİZ AI REHBER KÜTÜPHANESİ (LEAD MAGNET) (@Ai_gucum_)")
    print("=" * 70)

    with open(LEAD_MAGNET_JSON, "w", encoding="utf-8") as f:
        json.dump(VAULT_DATA, f, ensure_ascii=False, indent=2)

    with open(LEAD_MAGNET_HTML, "w", encoding="utf-8") as f:
        f.write(VAULT_HTML_TEMPLATE)

    print(f"✅ LEAD MAGNET JSON KAYDEDİLDİ: {LEAD_MAGNET_JSON}")
    print(f"✅ LEAD MAGNET MOBİL WEB SAYFASI KAYDEDİLDİ: {LEAD_MAGNET_HTML}")

if __name__ == "__main__":
    build_lead_magnet_vault()
