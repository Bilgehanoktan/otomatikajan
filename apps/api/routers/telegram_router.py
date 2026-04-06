"""
Telegram Webhook Router — Faz 4
Telegram bot'ından gelen güncellemeleri alır, bot.py'ye iletir.
GET /telegram/info    — Bot bilgisi ve yapılandırma durumu
POST /telegram/webhook — Telegram'dan gelen update (webhook modu)
POST /telegram/setup   — Webhook URL'ini Telegram'a kaydet
POST /telegram/send    — Manuel mesaj gönder (test/admin)
"""

import os
import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional

from apps.api.routers.auth.jwt_auth import require_admin, optional_admin, get_optional_user
from packages.observability.logging import get_logger

logger = get_logger("api.telegram")
router = APIRouter(prefix="/telegram", tags=["Telegram"])

BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")  # Telegram'ın gönderdiği secret token


# ── Bot durumu ─────────────────────────────────────────────
@router.get("/info", summary="Telegram bot bilgisi")
async def telegram_info():
    configured = bool(BOT_TOKEN)
    allowed_ids = list(filter(None, os.getenv("TELEGRAM_ALLOWED_IDS", "").split(",")))
    admin_ids   = list(filter(None, os.getenv("TELEGRAM_ADMIN_IDS", "").split(",")))

    result = {
        "configured":     configured,
        "allowed_count":  len(allowed_ids),
        "admin_count":    len(admin_ids),
        "webhook_secret": bool(WEBHOOK_SECRET),
    }

    if configured:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
                )
                data = resp.json()
                if data.get("ok"):
                    bot  = data["result"]
                    result["bot"] = {
                        "id":       bot["id"],
                        "username": bot.get("username"),
                        "name":     bot.get("first_name"),
                    }
                # Webhook bilgisi
                wresp = await client.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
                )
                wdata = wresp.json()
                if wdata.get("ok"):
                    result["webhook"] = wdata["result"]
        except Exception as e:
            result["error"] = str(e)

    return result


# ── Webhook kurulum ────────────────────────────────────────
@router.post("/setup", summary="Telegram webhook URL'ini ayarla", dependencies=[Depends(optional_admin)])
async def setup_webhook(body: dict):
    if not BOT_TOKEN:
        raise HTTPException(status_code=503, detail="TELEGRAM_BOT_TOKEN ayarlanmamış")

    webhook_url = body.get("url", "")
    if not webhook_url:
        raise HTTPException(status_code=422, detail="url gerekli")

    try:
        import httpx
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "edited_message"],
        }
        if WEBHOOK_SECRET:
            payload["secret_token"] = WEBHOOK_SECRET

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
                json=payload,
            )
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Webhook handler ────────────────────────────────────────
@router.post("/webhook", summary="Telegram güncellemelerini al", include_in_schema=False)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
):
    # Secret token doğrulama (Telegram, bu header'ı setup'ta verdiyseniz gönderir)
    if WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
            logger.warning("Telegram webhook: geçersiz secret token")
            raise HTTPException(status_code=403, detail="Geçersiz token")

    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz JSON")

    # Bot işleyici
    try:
        from telegram_app.bot import (
    handle_update,
    telegram_notifier,
    BOT_TOKEN,
    _tg_available,
    _is_admin,
    ALLOWED_IDS
)
        result = await handle_update(update_data)

        if result:
            chat_id, response_text, reply_markup = result
            await telegram_notifier.send_to_chat(chat_id, response_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Telegram webhook işleme hatası: {e}", exc_info=True)
        # Telegram'a 200 dönmeliyiz ki tekrar göndermeye çalışmasın
        return {"ok": True}

    return {"ok": True}


# ── Manuel mesaj gönder ────────────────────────────────────
@router.post("/send", summary="Belirli bir chat'e mesaj gönder (admin/test)", dependencies=[Depends(optional_admin)])
async def send_message(body: dict):
    if not BOT_TOKEN:
        raise HTTPException(status_code=503, detail="TELEGRAM_BOT_TOKEN ayarlanmamış")

    chat_id = body.get("chat_id")
    text    = body.get("text", "")
    if not chat_id or not text:
        raise HTTPException(status_code=422, detail="chat_id ve text gerekli")

    try:
        from telegram_app.bot import telegram_notifier
        success = await telegram_notifier.send_to_chat(int(chat_id), text)
        return {"sent": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Komut listesini Telegram'a kaydet ─────────────────────
@router.post("/register-commands", summary="Komutları Telegram'a kaydet", dependencies=[Depends(optional_admin)])
async def register_commands():
    if not BOT_TOKEN:
        raise HTTPException(status_code=503, detail="TELEGRAM_BOT_TOKEN ayarlanmamış")

    commands = [
        {"command": "start",    "description": "Botu başlat"},
        {"command": "help",     "description": "Komut listesi"},
        {"command": "status",   "description": "Sistem durumu"},
        {"command": "tasks",    "description": "Son görevler"},
        {"command": "task",     "description": "Görev detayı: /task <id>"},
        {"command": "newtask",  "description": "Yeni görev: /newtask başlık | açıklama"},
        {"command": "agents",   "description": "Ajan durumu"},
        {"command": "logs",     "description": "Son sistem logları"},
        {"command": "errors",   "description": "Son hatalar"},
        {"command": "queue",    "description": "Kuyruk durumu"},
        {"command": "metrics",  "description": "Performans metrikleri"},
        {"command": "audit",    "description": "Repo denetimi (ECC Audit)"},
    ]
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands",
                json={"commands": commands},
            )
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Yetkili kullanıcı listesi ──────────────────────────────
@router.get("/users", summary="Telegram kullanıcıları", dependencies=[Depends(optional_admin)])
async def list_telegram_users():
    try:
        from db.session import AsyncSessionLocal
        from db.repositories.repository import TelegramRepository
        async with AsyncSessionLocal() as db:
            users = await TelegramRepository.list_users(db)
        return [
            {
                "id":           str(u.id),
                "telegram_id":  u.telegram_id,
                "username":     u.username,
                "full_name":    u.full_name,
                "is_authorized":u.is_authorized,
                "is_admin":     u.is_admin,
                "command_count":u.command_count,
                "last_seen_at": u.last_seen_at.isoformat() if u.last_seen_at else None,
                "created_at":   u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    except Exception as e:
        return {"error": str(e), "users": []}


# ── Kullanıcı yetkilendir ──────────────────────────────────
@router.post("/users/{telegram_id}/authorize", summary="Kullanıcıyı yetkilendir", dependencies=[Depends(optional_admin)])
async def authorize_user(telegram_id: str, body: dict = {}):
    is_admin = body.get("is_admin", False)
    try:
        from db.session import AsyncSessionLocal
        from db.repositories.repository import TelegramRepository
        async with AsyncSessionLocal() as db:
            success = await TelegramRepository.authorize(db, telegram_id, is_admin=is_admin)
            await db.commit()
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Kullanıcı bulunamadı. Önce /start göndermesi gerekiyor."
            )
        return {"authorized": True, "telegram_id": telegram_id, "is_admin": is_admin}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
