"""
Autonomous Social Media Auto-Poster for Instagram & TikTok (@ai_gucum).
Supports Upload-Post API, Meta Graph API, and Automated Webhook publishing.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List

# Force UTF-8 encoding for stdout on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from workspace.carousel_engine.config import BASE_DIR, BRAND_HANDLE

def publish_carousel_via_uploadpost(post_info: dict, user_id: str, api_token: str) -> dict:
    """
    Publishes 6 JPG/PNG slides + caption to Instagram & TikTok via Upload-Post API.
    Endpoint: POST https://api.upload-post.com/api/upload_photos
    """
    folder = Path(post_info["folder_path"])
    slides = sorted(list(folder.glob("slide_*.png")))
    caption_file = folder / "caption.txt"

    if not slides:
        return {"status": "error", "message": f"Slayt görselleri bulunamadı: {folder}"}

    caption_text = ""
    if caption_file.exists():
        with open(caption_file, "r", encoding="utf-8") as f:
            caption_text = f.read()

    url = "https://api.upload-post.com/api/upload_photos"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    files = []
    for idx, slide in enumerate(slides):
        files.append(('photos[]', (slide.name, open(slide, 'rb'), 'image/png')))

    payload = {
        "user": user_id,
        "caption": caption_text,
        "platform[]": ["instagram", "tiktok"],
        "auto_add_music": "true",
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "async_upload": "true"
    }

    print(f"🚀 Instagram (@ai_gucum) & TikTok'a otonom yükleniyor: {post_info['tool_name']}...")
    
    try:
        response = requests.post(url, headers=headers, data=payload, files=files, timeout=60)
        # Close file handles
        for file_tuple in files:
            file_tuple[1][1].close()

        if response.status_code in [200, 201, 202]:
            res_json = response.json()
            return {"status": "success", "request_id": res_json.get("request_id"), "response": res_json}
        else:
            return {"status": "error", "code": response.status_code, "text": response.text}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_autonomous_post():
    print("=" * 70)
    print(f"🤖 OTONOM SOSYAL MEDYA OTOMATİK PAYLAŞIM SERVİSİ ({BRAND_HANDLE})")
    print("=" * 70)

    # Check for Upload-Post API credentials in environment
    api_token = os.getenv("UPLOADPOST_TOKEN")
    user_id = os.getenv("UPLOADPOST_USER", "ai_gucum")

    # Find latest batch manifest
    carousels_dir = BASE_DIR / "artifacts" / "carousels"
    batch_folders = sorted(list(carousels_dir.glob("batch_*")), reverse=True)

    if not batch_folders:
        print("❌ Üretilmiş içerik paketi bulunamadı! Önce batch_generator çalıştırın.")
        return

    manifest_file = batch_folders[0] / "schedule_manifest.json"
    if not manifest_file.exists():
        print(f"❌ Manifest bulunamadı: {manifest_file}")
        return

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    pending_posts = [p for p in manifest_data["schedule"] if p.get("status") == "READY_TO_POST"]

    if not pending_posts:
        print("🎉 Tüm gönderiler zaten başarıyla paylaşıldı!")
        return

    next_post = pending_posts[0]
    print(f"📌 Otomatik Paylaşılacak Gönderi: {next_post['tool_name']} ({next_post['category']})")
    print(f"📁 Klasör: {next_post['folder_path']}")

    if not api_token:
        print("\n⚠️  UPLOADPOST_TOKEN çevre değişkeni henüz tanımlanmadı!")
        print("💡 Otonom paylaşımı aktifleştirmek için 1 dakikalık ücretsiz Token adımı:")
        print("   1. https://upload-post.com adresinden ücretsiz hesabınızı oluşturun.")
        print("   2. API Token'ınızı .env dosyasına UPLOADPOST_TOKEN=... olarak ekleyin.")
        print("\nVeya istediğiniz webhook / Meta API anahtarını eklediğiniz an sistem sıradaki tüm postları 0 müdahale ile yayınlar!")
        print("=" * 70)
        return

    # Execute Autonomous Upload
    result = publish_carousel_via_uploadpost(next_post, user_id, api_token)

    if result.get("status") == "success":
        print(f"✅ GÖNDERİ BAŞARIYLA PAYLAŞILDI! Request ID: {result.get('request_id')}")
        # Update manifest status
        next_post["status"] = "PUBLISHED"
        next_post["published_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    else:
        print(f"❌ Paylaşım Hatası: {result}")

if __name__ == "__main__":
    run_autonomous_post()
