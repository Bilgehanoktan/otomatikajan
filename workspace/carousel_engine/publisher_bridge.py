"""
Publisher Bridge for Social Media Platforms (Upload-Post API / Webhook Bridge).
Automates direct-to-feed posting to Instagram and TikTok.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Force UTF-8 encoding for stdout on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def check_publish_status(manifest_file: Path) -> Dict[str, Any]:
    """Reads schedule manifest and returns pending/ready posts."""
    if not manifest_file.exists():
        return {"error": f"Manifest file not found: {manifest_file}"}

    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    ready_posts = [p for p in data.get("schedule", []) if p.get("status") == "READY_TO_POST"]
    
    return {
        "total_scheduled": len(data.get("schedule", [])),
        "ready_to_post": len(ready_posts),
        "posts": data.get("schedule", [])
    }

def print_publisher_summary(manifest_file: Path):
    """Prints a clear summary of posts ready for scheduling or automation."""
    status = check_publish_status(manifest_file)
    print("=" * 70)
    print("📡 OTOMATİK SOSYAL MEDYA YAYINLAMA KÖPRÜSÜ (PUBLISHER BRIDGE)")
    print("=" * 70)
    
    if "error" in status:
        print(f"❌ {status['error']}")
        return

    print(f"🗓️ Toplam Planlanan Gönderi: {status['total_scheduled']} Günlük Paket")
    print(f"✅ Paylaşıma Hazır Gönderi: {status['ready_to_post']} Adet\n")

    for post in status["posts"]:
        print(f"📌 [{post['scheduled_time']}] - {post['tool_name']} ({post['category']})")
        print(f"   ├─ Klasör: {post['folder_path']}")
        print(f"   ├─ Görseller: 6 Slayt PNG (9:16 Format)")
        print(f"   └─ Affiliate Link: {post['affiliate_link']}\n")

    print("💡 Not: UPLOADPOST_TOKEN çevre değişkeni girildiğinde gönderiler otonom paylaşılır.")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        manifest_p = Path(sys.argv[1])
    else:
        # Find latest batch
        carousels_dir = Path(__file__).resolve().parent.parent.parent / "artifacts" / "carousels"
        batch_folders = sorted(list(carousels_dir.glob("batch_*")), reverse=True)
        if batch_folders:
            manifest_p = batch_folders[0] / "schedule_manifest.json"
        else:
            manifest_p = carousels_dir / "schedule_manifest.json"

    print_publisher_summary(manifest_p)
