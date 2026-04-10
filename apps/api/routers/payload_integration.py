import hashlib
import hmac
import json
import os
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

# We will create this service next
# from apps.api.services.content_sync import handle_payload_event
from packages.observability.logging import get_logger

logger = get_logger("api.payload_integration")
router = APIRouter(prefix="/integrations/payload", tags=["Payload Integration"])


class PayloadWebhookEvent(BaseModel):
    collection: str
    operation: str
    docId: Optional[Any] = None
    slug: Optional[str] = None
    status: Optional[str] = None
    updatedAt: Optional[str] = None
    payload: dict[str, Any] = {}


def _verify_signature(raw_body: bytes, signature: Optional[str]) -> None:
    secret = os.getenv("FASTAPI_PAYLOAD_WEBHOOK_SECRET", "")
    if not secret:
        logger.warning("FASTAPI_PAYLOAD_WEBHOOK_SECRET is not set. Skipping signature verification.")
        return

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook signature header is missing",
        )

    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        logger.error(f"Invalid webhook signature. Received: {signature}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook signature verification failed",
        )


@router.post("/webhook")
async def payload_webhook(
    request: Request,
    x_payload_signature: Optional[str] = Header(default=None),
):
    raw_body = await request.body()
    _verify_signature(raw_body, x_payload_signature)

    try:
        body = json.loads(raw_body.decode("utf-8"))
        event = PayloadWebhookEvent(**body)
    except Exception as exc:
        logger.error(f"Payload webhook parse error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse webhook body",
        ) from exc

    logger.info(
        f"Payload webhook received | collection={event.collection} "
        f"operation={event.operation} slug={event.slug}"
    )

    # Lazy import to avoid circular dependencies if any
    from apps.api.services.content_sync import handle_payload_event
    result = await handle_payload_event(event.dict())

    return {
        "ok": True,
        "received": {
            "collection": event.collection,
            "operation": event.operation,
            "slug": event.slug,
        },
        "sync": result,
    }
