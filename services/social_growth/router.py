"""FastAPI router for authenticated Meta webhook events."""

from __future__ import annotations

import logging
from typing import Protocol

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse

from services.social_growth.config import MetaSettings
from services.social_growth.contracts import OperationEvidence, OperationStatus
from services.social_growth.service import SocialGrowthService
from services.social_growth.webhook import (
    SignatureError,
    WebhookPayloadError,
    parse_comment_events,
    verify_challenge,
    verify_signature,
)

MAX_WEBHOOK_BODY_BYTES = 256 * 1024
MAX_EVENTS_PER_WEBHOOK = 100
logger = logging.getLogger(__name__)


class WebhookRateLimiter(Protocol):
    """Ingress rate-limiter contract."""

    def allow(self, client_key: str) -> bool:
        """Return whether a caller may process another webhook request."""


def build_meta_webhook_router(
    settings: MetaSettings,
    service: SocialGrowthService,
    *,
    live_actions_enabled: bool = False,
    rate_limiter: WebhookRateLimiter | None = None,
) -> APIRouter:
    """Build a webhook router whose external actions are disabled by default."""

    router = APIRouter(tags=["social-growth"])

    @router.get("/webhook", response_class=PlainTextResponse)
    async def webhook_challenge(request: Request) -> PlainTextResponse:
        try:
            challenge = verify_challenge(request.query_params, settings.verify_token)
        except SignatureError as exc:
            logger.warning("Meta webhook challenge rejected")
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return PlainTextResponse(challenge)

    @router.post("/webhook")
    async def webhook_event(
        request: Request,
        signature: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    ) -> dict[str, object]:
        client_key = request.client.host if request.client else "unknown"
        if rate_limiter is not None and not rate_limiter.allow(client_key):
            logger.warning("Meta webhook rate limit exceeded")
            raise HTTPException(status_code=429, detail="Webhook rate limit aşıldı")

        content_length = request.headers.get("content-length")
        if content_length and _exceeds_body_limit(content_length):
            raise HTTPException(status_code=413, detail="Webhook gövdesi çok büyük")
        body = await request.body()
        if len(body) > MAX_WEBHOOK_BODY_BYTES:
            raise HTTPException(status_code=413, detail="Webhook gövdesi çok büyük")
        try:
            verify_signature(body, signature, settings.app_secret)
            events = parse_comment_events(body)
        except SignatureError as exc:
            logger.warning("Meta webhook signature rejected")
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except WebhookPayloadError as exc:
            logger.warning("Meta webhook payload rejected")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if len(events) > MAX_EVENTS_PER_WEBHOOK:
            raise HTTPException(status_code=413, detail="Webhook event sayısı sınırı aşıyor")

        if live_actions_enabled:
            evidence = [service.handle_comment(event) for event in events]
        else:
            evidence = [
                OperationEvidence(
                    operation="comment_private_reply",
                    status=OperationStatus.BLOCKED,
                    reason="SOCIAL_GROWTH_LIVE_ACTIONS_APPROVED etkin değil",
                    metadata={"comment_id": event.comment_id},
                )
                for event in events
            ]
        return {
            "received": len(events),
            "results": [_serialize_evidence(item) for item in evidence],
        }

    return router


def _exceeds_body_limit(content_length: str) -> bool:
    try:
        return int(content_length) > MAX_WEBHOOK_BODY_BYTES
    except ValueError:
        return True


def _serialize_evidence(evidence: OperationEvidence) -> dict[str, object]:
    return {
        "operation": evidence.operation,
        "status": evidence.status.value,
        "provider_id": evidence.provider_id,
        "reason": evidence.reason,
        "metadata": evidence.metadata,
        "occurred_at": evidence.occurred_at.isoformat(),
    }
