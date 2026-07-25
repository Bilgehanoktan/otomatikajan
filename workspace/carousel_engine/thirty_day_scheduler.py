"""
30-Day Rhythm & Publishing Time Experiment Scheduler for @ai_gucum_.
Schedules 30 days of strategic content with A/B Time Experiments:
- Window A: 12:30 Europe/Istanbul (TSI)
- Window B: 20:30 Europe/Istanbul (TSI)

Weekly Rhythm Rules:
- 3 Core Posts per week (2 Reels, 1 Carousel)
- 4-6 Story days (Polls, Quizzes, Process Behind-the-Scenes)
- Maximum 1 pure news post per week
- No back-to-back same day multiple feed posts
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKLOG_DB_PATH = BASE_DIR / "artifacts" / "carousels" / "official_backlog_db.json"
SCHEDULE_CALENDAR_PATH = BASE_DIR / "artifacts" / "carousels" / "thirty_day_schedule_calendar.json"

TIME_WINDOWS = {
    "WINDOW_A": "12:30 Europe/Istanbul",
    "WINDOW_B": "20:30 Europe/Istanbul"
}

def generate_30_day_calendar() -> List[Dict[str, Any]]:
    """Loads backlog topics and schedules them across 30 days alternating between 12:30 and 20:30 TSI."""
    if not BACKLOG_DB_PATH.exists():
        raise FileNotFoundError(f"Backlog DB not found at {BACKLOG_DB_PATH}")

    with open(BACKLOG_DB_PATH, "r", encoding="utf-8") as f:
        backlog_data = json.load(f)

    topics = backlog_data.get("backlog_topics", [])
    calendar = []

    # Map topics to the 30-day plan schedule
    day_map = [
        {"day": 1, "action": "Profil Fotoğrafı, Ad Alanı ve Link Düzelt", "format": "profile_repair", "topic_id": None},
        {"day": 2, "action": "Üç Highlight Kapakları & Başla Story", "format": "story", "topic_id": None},
        {"day": 3, "action": "Hesap Vaadi", "format": "pinned_carousel", "topic_id": None},
        {"day": 4, "action": "Takipçiye Konu Seçtir", "format": "story_poll", "topic_id": None},
        {"day": 5, "action": "Claude Opus 5 Copilot", "format": "reel", "topic_id": "topic_001"},
        {"day": 6, "action": "Reel Yapım Ekranı", "format": "story", "topic_id": None},
        {"day": 7, "action": "GPT-5.6 Model Seçimi", "format": "carousel", "topic_id": "topic_006"},
        {"day": 8, "action": "İlk İki İçerik Insight Kontrolü", "format": "analytics", "topic_id": None},
        {"day": 9, "action": "GPT-Live Demo", "format": "reel", "topic_id": "topic_005"},
        {"day": 10, "action": "Sesli AI Kullanıyor Musun?", "format": "story_poll", "topic_id": None},
        {"day": 11, "action": "MCP Stateless", "format": "carousel", "topic_id": "topic_002"},
        {"day": 12, "action": "MCP Terim Mini Testi", "format": "story_quiz", "topic_id": None},
        {"day": 13, "action": "Copilot + Linear", "format": "reel", "topic_id": "topic_003"},
        {"day": 14, "action": "Haftalık Sonuç Özeti", "format": "story", "topic_id": None},
        {"day": 15, "action": "Yalnız Analiz, Feed Gönderisi Yok", "format": "analytics", "topic_id": None},
        {"day": 16, "action": "OpenAI Presence", "format": "carousel", "topic_id": "topic_004"},
        {"day": 17, "action": "Ajan Güvenliği Soru Kutusu", "format": "story", "topic_id": None},
        {"day": 18, "action": "Gemma 4 Yerel Demo", "format": "reel", "topic_id": "topic_007"},
        {"day": 19, "action": "Kurulum Hataları", "format": "story", "topic_id": None},
        {"day": 20, "action": "Copilot Auto Model Seçimi", "format": "carousel", "topic_id": "topic_008"},
        {"day": 21, "action": "Yeni Hook Trial Reel Testi", "format": "trial_reel", "topic_id": None},
        {"day": 22, "action": "Trial Reel Sonucu İncele", "format": "analytics", "topic_id": None},
        {"day": 23, "action": "Kazanan Trial Reel Paylaş", "format": "reel", "topic_id": None},
        {"day": 24, "action": "AI Company 18 Gönderi Audit Vakası", "format": "reel", "topic_id": "topic_009"},
        {"day": 25, "action": "Audit Bulgusu Quiz", "format": "story_quiz", "topic_id": None},
        {"day": 26, "action": "Çok Paylaşmak Büyümek Değildir", "format": "carousel", "topic_id": "topic_010"},
        {"day": 27, "action": "Üç Model Aynı Görev", "format": "reel", "topic_id": "topic_011"},
        {"day": 28, "action": "Sonraki Konu Seçimi", "format": "story_poll", "topic_id": None},
        {"day": 29, "action": "30 Günlük Şeffaf Sonuç", "format": "carousel", "topic_id": "topic_012"},
        {"day": 30, "action": "Kazanan Sütunu Belirle & Sonraki Ayı Üret", "format": "analytics", "topic_id": None}
    ]

    for item in day_map:
        window = TIME_WINDOWS["WINDOW_A"] if item["day"] % 2 == 1 else TIME_WINDOWS["WINDOW_B"]
        item["publishing_window"] = window
        calendar.append(item)

    with open(SCHEDULE_CALENDAR_PATH, "w", encoding="utf-8") as f:
        json.dump(calendar, f, ensure_ascii=False, indent=2)

    print(f"✅ 30 Günlük Yayın Takvimi Ve A/B Saat Deney Motoru Oluşturuldu ({SCHEDULE_CALENDAR_PATH})")
    return calendar

if __name__ == "__main__":
    cal = generate_30_day_calendar()
    print("   Örnek Günler:")
    for d in cal[4:8]:
        print(f"   ├─ Gün {d['day']}: {d['action']} ({d['format']}) -> {d['publishing_window']}")
