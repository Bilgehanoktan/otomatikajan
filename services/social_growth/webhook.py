"""Meta webhook challenge, signature verification, and event normalization."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from typing import Any

from services.social_growth.service import CommentEvent

SIGNATURE_PREFIX = "sha256="


class SignatureError(ValueError):
    """Raised when a webhook body cannot be authenticated."""


class WebhookPayloadError(ValueError):
    """Raised when the authenticated webhook body is malformed."""


def verify_challenge(query: Mapping[str, str], expected_token: str) -> str:
    """Validate Meta's subscription challenge without leaking the verify token."""

    mode = query.get("hub.mode", "")
    token = query.get("hub.verify_token", "")
    challenge = query.get("hub.challenge", "")
    if mode != "subscribe" or not hmac.compare_digest(token, expected_token):
        raise SignatureError("Webhook challenge doğrulanamadı")
    if not challenge:
        raise SignatureError("Webhook challenge eksik")
    return challenge


def verify_signature(body: bytes, signature_header: str | None, app_secret: str) -> None:
    """Verify X-Hub-Signature-256 over the exact raw request body."""

    if not signature_header or not signature_header.startswith(SIGNATURE_PREFIX):
        raise SignatureError("Geçerli X-Hub-Signature-256 başlığı gerekli")
    supplied = signature_header[len(SIGNATURE_PREFIX) :]
    if len(supplied) != hashlib.sha256().digest_size * 2:
        raise SignatureError("Webhook imza uzunluğu geçersiz")
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied, expected):
        raise SignatureError("Webhook imzası geçersiz")


def parse_comment_events(body: bytes) -> list[CommentEvent]:
    """Normalize authenticated Instagram comment webhook changes."""

    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebhookPayloadError("Webhook gövdesi geçerli JSON değil") from exc
    if not isinstance(payload, dict):
        raise WebhookPayloadError("Webhook gövdesi nesne biçiminde değil")

    events: list[CommentEvent] = []
    for entry in _list(payload.get("entry")):
        for change in _list(entry.get("changes")):
            if change.get("field") != "comments":
                continue
            value = change.get("value")
            if not isinstance(value, dict):
                continue
            comment_id = value.get("id")
            text = value.get("text")
            if not isinstance(comment_id, str) or not isinstance(text, str):
                continue
            author = value.get("from")
            username = author.get("username") if isinstance(author, dict) else None
            events.append(
                CommentEvent(
                    comment_id=comment_id,
                    text=text,
                    username=username if isinstance(username, str) else None,
                )
            )
    return events


def _list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
