"""
Main Entry Point to Run the Autonomous Carousel Pipeline.
Generates full 6-slide Instagram/TikTok visual carousel and post caption.
"""

import os
import sys
from pathlib import Path

# Force UTF-8 encoding for stdout on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from workspace.carousel_engine.config import OUTPUT_DIR, DEFAULT_HASHTAGS
from workspace.carousel_engine.tool_researcher import get_target_tool_data
from workspace.carousel_engine.slide_generator import generate_carousel_slides
from workspace.carousel_engine.image_creator import render_slide

def generate_social_caption(tool_data: dict) -> str:
    """Generates an engaging, high-converting social media caption."""
    hashtags_str = " ".join(DEFAULT_HASHTAGS)
    
    caption = f"""🚀 Günde 3 saat tasarruf ettiren harika bir yapay zeka aracı keşfettim: {tool_data['name']}!

💻 Saatlerce spagetti kod ayıklamak ve karmaşık hatalarla boğuşmak yerine, tüm projenizi yapay zeka ile 10 kat daha hızlı kodlayabilirsiniz.

✨ Öne Çıkan Özellikler:
• ⚡ Composer: Tüm projeyi tek bir komutla düzenleyin
• 🔍 Kod Tabanı İle Sohbet (@Codebase): Binlerce satırlık koda soru sorun
• 🛡️ Otonom Hata Düzeltme: Terminal hatalarını tek tıkla çözün

🎁 Ücretsiz Deneme Linki Profildeki Bağlantıda! 🔗
Kaydetmeyi ve yazılımcı arkadaşlarınızla paylaşmayı unutmayın 🔖

{hashtags_str}
"""
    return caption

def main():
    print("=" * 60)
    print("🚀 Otonom Carousel & Affiliate Gelir Motoru Çalıştırılıyor...")
    print("=" * 60)

    # 1. Get Target Tool Data
    tool_data = get_target_tool_data("Cursor AI")
    print(f"📌 Hedef Araç: {tool_data['name']}")

    # 2. Generate 6 Slide Narrative Structure
    slides = generate_carousel_slides(tool_data)
    print(f"📊 {len(slides)} adet slayt mimarisi oluşturuldu.")

    # 3. Render 6 PNG Images
    print("🎨 Görseller 9:16 (768x1376) dikey formatta çiziliyor...")
    rendered_files = []
    for slide in slides:
        file_path = render_slide(slide, total_slides=len(slides))
        rendered_files.append(file_path)
        print(f"   ✅ Slayt {slide['slide_number']} oluşturuldu: {file_path}")

    # 4. Generate Caption Text
    caption = generate_social_caption(tool_data)
    caption_path = OUTPUT_DIR / "caption.txt"
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(caption)

    print("=" * 60)
    print(f"🎉 BAŞARILI! Tüm görseller ve açıklama metni hazırlandı.")
    print(f"📁 Çıktı Dizini: {OUTPUT_DIR}")
    print(f"📝 Açıklama Dosyası: {caption_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
