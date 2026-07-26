"""Deterministic post-quality audit with a grounded AI Company review gate."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Protocol
from urllib.parse import urlparse

INSTAGRAM_HOSTS = frozenset({"instagram.com", "www.instagram.com"})
MEDIA_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,128}$")
WORD_PATTERN = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9]+")
MIXED_CASE_PATTERN = re.compile(r"[a-zçğıöşü][A-ZÇĞİÖŞÜ]")
MAX_POSTS_PER_AUDIT = 25
BURST_THRESHOLD = 3
BURST_WINDOW_MINUTES = 90
BANNED_ACTION_TERMS = (
    "sil",
    "yayınla",
    "paylaş",
    "yorum yap",
    "dm gönder",
)


class FindingSeverity(str, Enum):
    """Deterministic finding severity."""

    INFO = "INFO"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AIReviewStatus(str, Enum):
    """Grounded AI review state."""

    REVIEWED = "REVIEWED"
    BLOCKED_AI_REVIEW = "BLOCKED_AI_REVIEW"


@dataclass(frozen=True)
class PostSnapshot:
    """Secret-free observation of one owned Instagram post."""

    media_id: str
    permalink: str
    timestamp: datetime
    media_type: str
    caption: str | None = None
    comment_count: int | None = None
    alt_text: str | None = None

    def __post_init__(self) -> None:
        if not MEDIA_ID_PATTERN.fullmatch(self.media_id):
            raise ValueError("media_id geçersiz")
        parsed = urlparse(self.permalink)
        if parsed.scheme != "https" or parsed.hostname not in INSTAGRAM_HOSTS:
            raise ValueError("permalink resmi HTTPS Instagram URL'si olmalı")
        if "/p/" not in parsed.path and "/reel/" not in parsed.path:
            raise ValueError("permalink post veya reel yolu olmalı")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp timezone-aware olmalı")
        if not self.media_type.strip():
            raise ValueError("media_type boş olamaz")
        if self.comment_count is not None and self.comment_count < 0:
            raise ValueError("comment_count negatif olamaz")

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> PostSnapshot:
        """Build a validated snapshot from Meta or an operator evidence file."""

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("timestamp ISO-8601 biçiminde olmalı") from exc
        if not isinstance(timestamp, datetime):
            raise ValueError("timestamp zorunludur")
        return cls(
            media_id=str(data.get("id") or data.get("media_id") or ""),
            permalink=str(data.get("permalink") or ""),
            timestamp=timestamp,
            media_type=str(data.get("media_type") or ""),
            caption=_optional_string(data.get("caption")),
            comment_count=_optional_integer(
                data.get("comments_count", data.get("comment_count"))
            ),
            alt_text=_optional_string(data.get("alt_text")),
        )


@dataclass(frozen=True)
class AuditFinding:
    """One traceable deterministic content issue."""

    code: str
    severity: FindingSeverity
    post_ids: tuple[str, ...]
    evidence: str
    recommendation: str


@dataclass(frozen=True)
class DeterministicAuditReport:
    """Model-independent audit result used as the AI review source of truth."""

    posts: tuple[PostSnapshot, ...]
    findings: tuple[AuditFinding, ...]
    score: int
    input_fingerprint: str

    @property
    def posts_checked(self) -> int:
        return len(self.posts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "posts_checked": self.posts_checked,
            "score": self.score,
            "input_fingerprint": self.input_fingerprint,
            "posts": [
                {
                    "media_id": post.media_id,
                    "permalink": post.permalink,
                    "timestamp": post.timestamp.isoformat(),
                    "media_type": post.media_type,
                    "caption": post.caption,
                    "comment_count": post.comment_count,
                    "alt_text": post.alt_text,
                }
                for post in self.posts
            ],
            "findings": [
                {
                    "code": finding.code,
                    "severity": finding.severity.value,
                    "post_ids": list(finding.post_ids),
                    "evidence": finding.evidence,
                    "recommendation": finding.recommendation,
                }
                for finding in self.findings
            ],
        }


@dataclass(frozen=True)
class AIReviewPriority:
    """AI-proposed action grounded to one deterministic finding."""

    post_id: str
    issue_code: str
    action: str


@dataclass(frozen=True)
class DraftIdea:
    """Non-publishing content draft concept."""

    hook: str
    format: str
    cta: str


@dataclass(frozen=True)
class AIReviewResult:
    """Validated AI Company review output."""

    status: AIReviewStatus
    summary: str = ""
    priorities: tuple[AIReviewPriority, ...] = ()
    draft_ideas: tuple[DraftIdea, ...] = ()
    blocked_reason: str | None = None


class ReviewGateway(Protocol):
    """AI Company reviewer adapter contract."""

    def review(self, prompt: str) -> str:
        """Return a JSON-only review."""


def audit_posts(posts: list[PostSnapshot]) -> DeterministicAuditReport:
    """Run deterministic rules without inventing engagement or visual metrics."""

    if not posts:
        raise ValueError("Audit için en az bir post gerekli")
    if len(posts) > MAX_POSTS_PER_AUDIT:
        raise ValueError("Bir audit en fazla 25 post içerebilir")

    findings: list[AuditFinding] = []
    for post in posts:
        findings.extend(_audit_post(post))
    burst = _find_posting_burst(posts)
    if burst:
        findings.append(burst)

    penalty = sum(_penalty(finding.severity) for finding in findings)
    fingerprint = _fingerprint(posts)
    return DeterministicAuditReport(
        posts=tuple(posts),
        findings=tuple(findings),
        score=max(0, 100 - penalty),
        input_fingerprint=fingerprint,
    )


class AICompanyPostAuditor:
    """Accept only grounded JSON from an AI Company review agent."""

    def __init__(self, gateway: ReviewGateway) -> None:
        self._gateway = gateway

    def review(self, report: DeterministicAuditReport) -> AIReviewResult:
        prompt = _build_review_prompt(report)
        try:
            raw = self._gateway.review(prompt)
            payload = _decode_json_response(raw)
            return _validate_ai_payload(payload, report)
        except (ValueError, TypeError, json.JSONDecodeError, RuntimeError) as exc:
            return AIReviewResult(
                status=AIReviewStatus.BLOCKED_AI_REVIEW,
                blocked_reason=f"{type(exc).__name__}: {exc}",
            )


def _decode_json_response(raw: str) -> Any:
    if not isinstance(raw, str) or len(raw) > 65_536:
        raise ValueError("AI review metni geçersiz veya çok büyük")
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) < 3 or lines[0].casefold() not in {"```", "```json"}:
            raise ValueError("AI review code fence biçimi geçersiz")
        if lines[-1].strip() != "```":
            raise ValueError("AI review code fence kapanmıyor")
        cleaned = "\n".join(lines[1:-1]).strip()
    return json.loads(cleaned)


def _audit_post(post: PostSnapshot) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    if not post.caption or not post.caption.strip():
        findings.append(
            AuditFinding(
                code="MISSING_CAPTION",
                severity=FindingSeverity.HIGH,
                post_ids=(post.media_id,),
                evidence="caption alanı boş veya gözlenemedi",
                recommendation="Hook, değer önerisi ve tek CTA içeren caption taslağı üret.",
            )
        )
    if post.comment_count is None:
        findings.append(
            AuditFinding(
                code="COMMENT_SIGNAL_UNKNOWN",
                severity=FindingSeverity.INFO,
                post_ids=(post.media_id,),
                evidence="comment_count kaynağı mevcut değil",
                recommendation="Meta Insights erişimiyle yorum sayısını doğrula.",
            )
        )
    elif post.comment_count == 0:
        findings.append(
            AuditFinding(
                code="NO_COMMENT_SIGNAL",
                severity=FindingSeverity.MEDIUM,
                post_ids=(post.media_id,),
                evidence="comment_count=0",
                recommendation="Caption içinde cevaplanabilir tek bir soru veya CTA kullan.",
            )
        )
    if _has_visual_text_risk(post.alt_text):
        findings.append(
            AuditFinding(
                code="VISUAL_TEXT_RISK",
                severity=FindingSeverity.HIGH,
                post_ids=(post.media_id,),
                evidence="alt_text tekrar veya bozuk karma-büyük/küçük harf sinyali içeriyor",
                recommendation="Yayın öncesi OCR ve insan gözü kalite geçidi çalıştır.",
            )
        )
    return findings


def _find_posting_burst(posts: list[PostSnapshot]) -> AuditFinding | None:
    ordered = sorted(posts, key=lambda post: post.timestamp)
    window = timedelta(minutes=BURST_WINDOW_MINUTES)
    for index in range(len(ordered) - BURST_THRESHOLD + 1):
        candidates = ordered[index : index + BURST_THRESHOLD]
        if candidates[-1].timestamp - candidates[0].timestamp <= window:
            return AuditFinding(
                code="POSTING_BURST_RISK",
                severity=FindingSeverity.HIGH,
                post_ids=tuple(post.media_id for post in candidates),
                evidence=(
                    f"{BURST_THRESHOLD} gönderi {BURST_WINDOW_MINUTES} dakika "
                    "içinde yayınlandı"
                ),
                recommendation="Gönderileri ayrı test pencerelerine yay ve sonucu ölç.",
            )
    return None


def _has_visual_text_risk(alt_text: str | None) -> bool:
    if not alt_text:
        return False
    tokens = WORD_PATTERN.findall(alt_text)
    normalized = [token.casefold() for token in tokens if len(token) > 2]
    duplicate_count = sum(count - 1 for count in Counter(normalized).values() if count > 1)
    mixed_case_count = sum(bool(MIXED_CASE_PATTERN.search(token)) for token in tokens)
    return "�" in alt_text or duplicate_count >= 4 or mixed_case_count >= 3


def _fingerprint(posts: list[PostSnapshot]) -> str:
    canonical = [
        {
            "media_id": post.media_id,
            "permalink": post.permalink,
            "timestamp": post.timestamp.isoformat(),
            "media_type": post.media_type,
            "caption": post.caption,
            "comment_count": post.comment_count,
            "alt_text": post.alt_text,
        }
        for post in posts
    ]
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _penalty(severity: FindingSeverity) -> int:
    return {
        FindingSeverity.INFO: 0,
        FindingSeverity.MEDIUM: 8,
        FindingSeverity.HIGH: 15,
    }[severity]


def _build_review_prompt(report: DeterministicAuditReport) -> str:
    schema = {
        "summary": "string",
        "priorities": [
            {"post_id": "known id", "issue_code": "known code", "action": "draft-only action"}
        ],
        "draft_ideas": [{"hook": "string", "format": "string", "cta": "string"}],
    }
    return (
        "AI Gücüm post auditini reviewer olarak değerlendir. Yalnız JSON döndür. "
        "Yeni metrik uydurma; yalnız verilen post_id ve issue_code değerlerini kullan. "
        "Silme, yayınlama, paylaşma, yorum veya DM eylemi önerme; yalnız taslak ve "
        "kalite iyileştirmesi üret.\n"
        f"SCHEMA={json.dumps(schema, ensure_ascii=False)}\n"
        f"AUDIT={json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True)}"
    )


def _validate_ai_payload(
    payload: Any,
    report: DeterministicAuditReport,
) -> AIReviewResult:
    if not isinstance(payload, dict):
        raise ValueError("AI review nesne biçiminde olmalı")
    summary = _bounded_text(payload.get("summary"), "summary", 2_000)
    raw_priorities = payload.get("priorities")
    raw_ideas = payload.get("draft_ideas")
    if not isinstance(raw_priorities, list) or len(raw_priorities) > 20:
        raise ValueError("priorities geçerli bir liste olmalı")
    if not isinstance(raw_ideas, list) or len(raw_ideas) > 10:
        raise ValueError("draft_ideas geçerli bir liste olmalı")

    known_post_ids = {post.media_id for post in report.posts}
    known_codes = {finding.code for finding in report.findings}
    priorities = tuple(
        _validate_priority(item, known_post_ids, known_codes) for item in raw_priorities
    )
    ideas = tuple(_validate_idea(item) for item in raw_ideas)
    return AIReviewResult(
        status=AIReviewStatus.REVIEWED,
        summary=summary,
        priorities=priorities,
        draft_ideas=ideas,
    )


def _validate_priority(
    item: Any,
    known_post_ids: set[str],
    known_codes: set[str],
) -> AIReviewPriority:
    if not isinstance(item, dict):
        raise ValueError("priority nesne biçiminde olmalı")
    post_id = _bounded_text(item.get("post_id"), "post_id", 128)
    issue_code = _bounded_text(item.get("issue_code"), "issue_code", 128)
    action = _bounded_text(item.get("action"), "action", 500)
    if post_id not in known_post_ids:
        raise ValueError("priority bilinmeyen post_id içeriyor")
    if issue_code not in known_codes:
        raise ValueError("priority bilinmeyen issue_code içeriyor")
    if any(term in action.casefold() for term in BANNED_ACTION_TERMS):
        raise ValueError("priority dış etki öneriyor")
    return AIReviewPriority(post_id=post_id, issue_code=issue_code, action=action)


def _validate_idea(item: Any) -> DraftIdea:
    if not isinstance(item, dict):
        raise ValueError("draft idea nesne biçiminde olmalı")
    return DraftIdea(
        hook=_bounded_text(item.get("hook"), "hook", 300),
        format=_bounded_text(item.get("format"), "format", 100),
        cta=_bounded_text(item.get("cta"), "cta", 200),
    )


def _bounded_text(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} boş olmayan string olmalı")
    cleaned = value.strip()
    if len(cleaned) > maximum:
        raise ValueError(f"{field} uzunluk sınırını aşıyor")
    return cleaned


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("string alanı geçersiz")
    return value


def _optional_integer(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("integer alanı geçersiz")
    return value
