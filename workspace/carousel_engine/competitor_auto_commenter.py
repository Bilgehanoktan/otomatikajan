"""Policy-blocked legacy competitor comment planner."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
COMPETITOR_LOG_FILE = (
    BASE_DIR / "artifacts" / "carousels" / "competitor_comments_log.json"
)

COMPETITOR_TARGETS = [
    {"handle": "@therundownai", "topic": "AI News & Tools"},
    {"handle": "@superhuman.ai", "topic": "Productivity Hacks"},
    {"handle": "@futurepedia", "topic": "AI Directory"},
    {"handle": "@yapayzekarehberi", "topic": "Türkçe Yapay Zeka"},
]

HIGH_VALUE_COMMENTS_POOL = [
    "DeepSeek R1 için ayrıntılı Türkçe inceleme taslağı.",
    "Bolt.new ile uygulama üretimi için kodlama ipuçları taslağı.",
    "Flux görsel üretimi için örnek prompt taslağı.",
    "Yapay zeka ses üretimi için Türkçe rehber taslağı.",
]


def auto_comment_on_competitor_posts() -> list[dict[str, Any]]:
    """Create human-review proposals and never post promotional comments."""

    results: list[dict[str, Any]] = []
    for index, target in enumerate(COMPETITOR_TARGETS):
        comment_text = HIGH_VALUE_COMMENTS_POOL[index % len(HIGH_VALUE_COMMENTS_POOL)]
        entry = {
            "planned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_account": target["handle"],
            "topic": target["topic"],
            "comment_text": comment_text,
            "status": "BLOCKED_POLICY",
            "reason": "Otomatik tanıtım yorumu gönderilmez; insan incelemesi gerekli",
        }
        results.append(entry)
        print(f"BLOCKED [{target['handle']}] -> Taslak: \"{comment_text}\"")

    COMPETITOR_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    COMPETITOR_LOG_FILE.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return results


if __name__ == "__main__":
    auto_comment_on_competitor_posts()
