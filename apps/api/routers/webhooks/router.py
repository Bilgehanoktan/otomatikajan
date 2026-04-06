"""
Webhook Yönetimi
• Abonelik oluşturma / silme / listeleme
• HMAC-SHA256 imza doğrulama
• Desteklenen olaylar: project.*, agent.*, system.*
"""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.routers.apps.api.routers.auth.jwt_auth import get_current_user
from packages.persistence.models import User, WebhookSubscription
from packages.persistence.session import get_db_dep

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

SUPPORTED_EVENTS = {
    "project.completed", "project.failed", "project.started",
    "agent.failed", "agent.recovered",
    "system.health_critical", "system.budget_warning",
    "*",  # Tüm olaylar
}


class WebhookCreate(BaseModel):
    url:    HttpUrl
    events: list[str]


class WebhookOut(BaseModel):
    id:       str
    url:      str
    events:   list[str]
    is_active: bool


@router.post("", response_model=WebhookOut)
async def create_webhook(
    body: WebhookCreate,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db_dep),
):
    invalid = [e for e in body.events if e not in SUPPORTED_EVENTS]
    if invalid:
        raise HTTPException(400, f"Geçersiz olaylar: {invalid}. Desteklenenler: {SUPPORTED_EVENTS}")

    sub = WebhookSubscription(
        owner_id=user.id,
        url=str(body.url),
        events=body.events,
        secret=secrets.token_hex(32),
    )
    packages.persistence.add(sub)
    await packages.persistence.flush()
    return WebhookOut(id=str(sub.id), url=sub.url, events=sub.events, is_active=sub.is_active)


@router.get("", response_model=list[WebhookOut])
async def list_webhooks(
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db_dep),
):
    subs = (await packages.persistence.execute(
        select(WebhookSubscription).where(WebhookSubscription.owner_id == user.id)
    )).scalars().all()
    return [WebhookOut(id=str(s.id), url=s.url, events=s.events, is_active=s.is_active) for s in subs]


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    user: User = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db_dep),
):
    sub = (await packages.persistence.execute(
        select(WebhookSubscription)
        .where(WebhookSubscription.id == webhook_id)
        .where(WebhookSubscription.owner_id == user.id)
    )).scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Webhook bulunamadı.")
    sub.is_active = False
    return {"deleted": True}


# ── WebhookRouter: HMAC imzalı delivery (test uyumluluğu) ──
import hashlib
import hmac
import json as _json
import httpx


class WebhookRouter:
    """Webhook teslim motoru — HMAC-SHA256 imzalı HTTP POST gönderir."""

    async def _send(
        self,
        subscription,
        event_type: str,
        payload: dict,
    ) -> bool:
        """
        Tek bir webhook aboneliğine event gönder.
        Header: X-Webhook-Signature: sha256=<hmac>
        """
        body    = _json.dumps({"event": event_type, **payload}, default=str).encode()
        secret  = getattr(subscription, "secret", "") or ""
        sig     = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        headers = {
            "Content-Type":         "application/json",
            "X-Webhook-Signature":  f"sha256={sig}",
            "X-Webhook-Event":      event_type,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    str(subscription.url),
                    json={"event": event_type, **payload},
                    headers=headers,
                    timeout=10.0,
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Webhook delivery failed: {e}")
            return False

    async def dispatch(self, db, event_type: str, payload: dict):
        """Tüm aktif aboneliklere event gönder."""
        from sqlalchemy import select
        from packages.persistence.models import WebhookSubscription

        subs = (await packages.persistence.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.is_active == True,
            )
        )).scalars().all()

        for sub in subs:
            if "*" in sub.events or event_type in sub.events:
                await self._send(sub, event_type, payload)
