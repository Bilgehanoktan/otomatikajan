"""Run a secret-free Instagram post audit through AI Company's reviewer role."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from libs.llm.model_orchestrator import ModelOrchestrator
from services.social_growth.content_auditor import (
    AICompanyPostAuditor,
    AIReviewResult,
    DeterministicAuditReport,
    PostSnapshot,
    ReviewGateway,
    audit_posts,
)

MAX_SNAPSHOT_BYTES = 1024 * 1024
SYSTEM_PROMPT = (
    "Sen AI Company reviewer ajanısın. Yalnız kullanıcı mesajındaki audit kanıtına "
    "dayan. Yalnız geçerli JSON döndür; Markdown veya açıklama ekleme. Canlı işlem "
    "önerme. Gönderi silme, yayınlama, paylaşma, yorum ve DM işlemleri yasaktır."
)


class ModelOrchestratorReviewGateway(ReviewGateway):
    """Adapt the repository's own model orchestrator to the review contract."""

    def __init__(self) -> None:
        self._orchestrator = ModelOrchestrator()
        self.provider = os.getenv("SOCIAL_GROWTH_REVIEW_PROVIDER", "groq").strip()
        provider = self._orchestrator.providers.get(self.provider)
        if provider is None:
            raise ValueError("SOCIAL_GROWTH_REVIEW_PROVIDER bilinmiyor")
        if not provider.api_key or provider.is_placeholder_key():
            raise RuntimeError("Seçilen reviewer provider yapılandırılmamış")
        self.model_name = provider.model

    def review(self, prompt: str) -> str:
        return asyncio.run(
            self._orchestrator.complete(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                preferred_agent="reviewer",
                force_provider=self.provider,
            )
        )


def load_snapshot(path: Path) -> list[PostSnapshot]:
    """Load a bounded operator/Meta snapshot and validate every post."""

    if path.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise ValueError("Snapshot 1 MiB sınırını aşıyor")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("posts"), list):
        raise ValueError("Snapshot posts listesi içermelidir")
    return [PostSnapshot.from_mapping(item) for item in payload["posts"]]


def serialize_result(
    report: DeterministicAuditReport,
    review: AIReviewResult,
    gateway: ModelOrchestratorReviewGateway,
) -> dict[str, Any]:
    """Build a secret-free evidence object."""

    return {
        "audit": report.to_dict(),
        "ai_review": {
            "status": review.status.value,
            "summary": review.summary,
            "priorities": [
                {
                    "post_id": item.post_id,
                    "issue_code": item.issue_code,
                    "action": item.action,
                }
                for item in review.priorities
            ],
            "draft_ideas": [
                {"hook": item.hook, "format": item.format, "cta": item.cta}
                for item in review.draft_ideas
            ],
            "blocked_reason": review.blocked_reason,
            "agent_role": "reviewer",
            "provider": gateway.provider,
            "model_name": gateway.model_name,
        },
        "governance": {
            "live_actions": "BLOCKED",
            "allowed_output": "audit_and_drafts_only",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        posts = load_snapshot(args.input)
        report = audit_posts(posts)
        gateway = ModelOrchestratorReviewGateway()
        review = AICompanyPostAuditor(gateway).review(report)
        evidence = serialize_result(report, review, gateway)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, TypeError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"POST_AUDIT_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"POST_AUDIT_STATUS={review.status.value}")
    print(f"POST_AUDIT_SCORE={report.score}")
    print(f"POST_AUDIT_OUTPUT={args.output}")
    return 0 if review.status.value == "REVIEWED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
