"""Legacy comment-trigger planner that never sends a DM."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DM_LOG_FILE = BASE_DIR / "artifacts" / "carousels" / "dm_automation_log.json"

DM_TRIGGER_MAPPING = {
    "DEEPSEEK": "https://aigucum.notion.site/DeepSeek-R1-Gizli-Prompt-Rehberi",
    "BOLT": "https://aigucum.notion.site/Bolt-new-Web-App-Kurulum-Rehberi",
    "FLUX": "https://aigucum.notion.site/Flux-11-Pro-Ultra-Gorsel-Promptlari",
    "PROMPT": "https://aigucum.notion.site/50-Ucretsiz-Yapay-Zeka-Hilesi",
    "REELS": "https://aigucum.notion.site/Reels-Yapay-Zeka-Video-Seti",
}


def process_incoming_comment_triggers(
    comments_sample: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Plan replies for supplied samples without performing an external action."""

    if comments_sample is None:
        print("Doğrulanmış webhook olayı verilmedi; hiçbir mesaj gönderilmedi.")
        return []

    responses: list[dict[str, Any]] = []
    for comment in comments_sample:
        text_upper = comment["comment"].upper()
        matched_trigger = next(
            (trigger for trigger in DM_TRIGGER_MAPPING if trigger in text_upper),
            None,
        )
        if matched_trigger is None:
            responses.append(
                {
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "target_user": comment["username"],
                    "user_comment": comment["comment"],
                    "matched_trigger": None,
                    "status": "IGNORED",
                    "reason": "Eşleşen izinli tetikleyici yok",
                }
            )
            continue

        link = DM_TRIGGER_MAPPING[matched_trigger]
        responses.append(
            {
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "target_user": comment["username"],
                "user_comment": comment["comment"],
                "matched_trigger": matched_trigger,
                "proposed_dm_link": link,
                "status": "DRY_RUN",
                "reason": "Official Meta webhook ve provider evidence gerekli",
            }
        )
        print(
            f"DRY RUN -> @{comment['username']} | "
            f"Tetikleyici: '{matched_trigger}' | Link: {link}"
        )

    DM_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    DM_LOG_FILE.write_text(
        json.dumps(responses, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return responses


if __name__ == "__main__":
    process_incoming_comment_triggers()
