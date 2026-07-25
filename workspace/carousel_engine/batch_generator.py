"""
Batch Carousel Generator Module for @Ai_gucum_.
Generates 1080x1920 Ultra HD HTML/CSS 6-slide carousel sets from Trend Intelligence DB.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from workspace.carousel_engine.slide_generator import generate_carousel_slides
from workspace.carousel_engine.html_slide_renderer import render_slide_with_playwright
from workspace.carousel_engine.config import OUTPUT_DIR, BRAND_HANDLE

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TRENDS_CACHE_FILE = BASE_DIR / "artifacts" / "carousels" / "trend_intelligence.json"

def run_batch_generation():
    print("=" * 70)
    print("🚀 OTONOM ULTRA HD HTML/CSS TREND BATCH İÇERİK MOTORU (@Ai_gucum_)")
    print("=" * 70)

    # 1. Load tools from Trend Intelligence DB
    tools_list = []
    if TRENDS_CACHE_FILE.exists():
        with open(TRENDS_CACHE_FILE, "r", encoding="utf-8") as f:
            trend_db = json.load(f)
            tools_list = trend_db.get("top_trending_tools", [])

    if not tools_list:
        from workspace.carousel_engine.tool_researcher import POPULAR_AI_TOOLS
        tools_list = POPULAR_AI_TOOLS

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    batch_folder = OUTPUT_DIR / f"batch_{timestamp}"
    batch_folder.mkdir(parents=True, exist_ok=True)

    print(f"📦 Toplam {len(tools_list)} adet trend AI aracı işlenecek.")
    print(f"📁 Çıktı Klasörü: {batch_folder}\n")

    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_posts": len(tools_list),
        "total_slides": len(tools_list) * 6,
        "niche": "Yapay Zeka & Yazılım Araçları",
        "schedule": []
    }

    for idx, tool in enumerate(tools_list, 1):
        tool_folder_name = tool["name"].lower().replace(" ", "_").replace(".", "").replace("'", "")
        tool_folder = batch_folder / tool_folder_name
        tool_folder.mkdir(parents=True, exist_ok=True)

        print(f"[{idx}/{len(tools_list)}] 🎯 Üretiliyor: {tool['name']} ({tool['category']})")

        # Generate 6 viral slide definitions
        slides = generate_carousel_slides(tool)

        # Render 6 Ultra HD Playwright HTML images
        for slide in slides:
            output_png = tool_folder / f"slide_{slide['slide_number']}.png"
            rendered_path = render_slide_with_playwright(slide, output_png, total_slides=len(slides))
            print(f"   └─ Slayt {slide['slide_number']}/6 hazır (HTML/CSS Ultra HD): {Path(rendered_path).name}")

        # Create caption text
        caption_file = tool_folder / "caption.txt"
        trigger_word = tool["name"].upper().replace(" ", "")
        caption_content = (
            f"🔥 {tool['name'].upper()} - ChatGPT'yi Unutturan Yeni Nesil Yapay Zeka!\n\n"
            f"💡 Hedef Kitle: {tool.get('target_audience', 'Yazılımcılar & Üreticiler')}\n\n"
            f"📩 REHBERİ ANINDA ALIN:\n"
            f"Yorumlara '{trigger_word}' yazın, tüm giriş bağlantısını ve gizli kullanım rehberini mesaj olarak göndereyim!\n\n"
            f"❌ GELENEKSEL YÖNTEM:\n{tool['problem']}\n\n"
            f"⚡ DEVRİM ÇÖZÜM:\n{tool['solution']}\n\n"
            f"⭐ ÖNE ÇIKAN ÖZELLİKLER:\n"
        )

        for feat in tool.get("features", []):
            caption_content += f"• {feat['title']}: {feat['desc']}\n"

        caption_content += (
            f"\n🔗 BAĞLANTI & ERİŞİM:\n"
            f"Biyografimizdeki ({BRAND_HANDLE}) bağlantıya tıklayarak ücretsiz deneyebilirsiniz!\n\n"
            f"🔖 Kaydetmeyi ve takip etmeyi unutmayın!\n\n"
            f"#aigucum #{trigger_word.lower()} #yapayzeka #yazılım #kodlama #otomasyon #affiliatemarketing"
        )

        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(caption_content)

        manifest["schedule"].append({
            "post_id": idx,
            "tool_name": tool["name"],
            "category": tool["category"],
            "folder_path": str(tool_folder),
            "slides_count": len(slides),
            "caption_file": str(caption_file),
            "affiliate_link": tool.get("affiliate_link", f"https://{tool_folder_name}.ai/?ref=otomatikajan"),
            "status": "READY_TO_POST"
        })

    manifest_file = batch_folder / "schedule_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("🎉 BAŞARILI! HTML/CSS Trend İçerik Paketi ve Takvimi Oluşturuldu.")
    print(f"📊 Toplam Üretilen Post: {len(tools_list)} adet")
    print(f"📸 Toplam Üretilen HTML Ultra HD Slayt Görseli: {len(tools_list) * 6} adet")
    print(f"📁 İçerik Paketi Dizini: {batch_folder}")
    print(f"🗓️ Zamanlama Takvimi: {manifest_file}")
    print("=" * 70)

if __name__ == "__main__":
    run_batch_generation()
