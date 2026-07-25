"""
Phase B — Content Brief Generator for @ai_gucum_.
Generates strict JSON briefs adhering to the official schema:
{
  "topic": "",
  "audience": "",
  "claim": "",
  "source_urls": [],
  "format": "reel|carousel|story",
  "hook": "",
  "steps": [],
  "limitation": "",
  "cta": "",
  "visual_brief": ""
}
Blocks any ungrounded claim with BLOCKED_UNGROUNDED_CLAIM.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from workspace.carousel_engine.official_news_collector import is_allowlisted_url

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def generate_content_brief(topic_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a structured brief from topic data, validating grounding sources against allowlist."""
    source_url = topic_data.get("official_source_url", "")
    if not source_url or not is_allowlisted_url(source_url):
        return {
            "status": "BLOCKED_UNGROUNDED_CLAIM",
            "reason": f"Missing or unverified official source URL ({source_url}). Must belong to allowlisted official domain."
        }

    brief = {
        "status": "APPROVED",
        "topic": topic_data.get("title", ""),
        "audience": "Türkçe konuşan yazılımcılar, solo geliştiriciler & teknik AI uygulayıcıları",
        "claim": topic_data.get("hook", ""),
        "source_urls": [source_url],
        "format": topic_data.get("format", "carousel"),
        "hook": topic_data.get("hook", ""),
        "steps": [
            "1-2 sn: Problem veya Şok Edici Sonuç",
            "Detaylı Uygulamalı Ekran Kaydı veya Canlı Demo",
            "Neden Önemli ve Sınırlamalar",
            "3 Uygulanabilir Adım ve Kod/Prompt Örneği"
        ],
        "limitation": "Son sürüm teknik gereksinimler gerektirir. Kullanım alanına göre test ediniz.",
        "cta": topic_data.get("cta", "Detaylar için kaydet veya yorum yaz."),
        "visual_brief": "Dark Glassmorphism 4:5 (carousel) veya 9:16 (reel) 1080p yüksek kontrastlı tipografi."
    }

    return brief

if __name__ == "__main__":
    sample_topic = {
        "title": "Claude Opus 5 GitHub Copilot’ta",
        "hook": "Copilot’a bugün gelen model, uzun görevlerde neyi değiştiriyor?",
        "official_source_url": "https://github.blog/changelog/2026-07-24-claude-opus-5-is-now-available-in-github-copilot/",
        "format": "reel",
        "cta": "Bir repo göreviyle test etmemi istiyorsan 'TEST' yaz."
    }
    brief = generate_content_brief(sample_topic)
    print("✅ Phase B — Content Brief Generator Output:")
    print(json.dumps(brief, ensure_ascii=False, indent=2))
