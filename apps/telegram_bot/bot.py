import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger("telegram.bot")

# Load configuration from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Read allowed and admin IDs
ALLOWED_IDS = set(filter(None, os.getenv("TELEGRAM_ALLOWED_IDS", "").split(",")))
ADMIN_IDS = set(filter(None, os.getenv("TELEGRAM_ADMIN_IDS", "").split(",")))
RECIPIENTS = list(ALLOWED_IDS | ADMIN_IDS)

class TelegramNotifier:
    """
    Sistem olaylarında yetkili kullanıcılara bildirim gönderir.
    """

    NOTIFY_EVENTS = {
        "project.completed":        "✅ Görev tamamlandı",
        "project.failed":           "❌ Görev başarısız",
        "heal.critical":            "🔴 Kritik ajan sorunu",
        "system.cascade_fail":      "🚨 Sistem kaskat hatası",
        "approval.needed":          "⏳ Onay bekleniyor",
        "packages.repair_engine.incident_created":  "🚨 Yeni Incident",
        "packages.repair_engine.job_started":       "⚙️ Repair Job Başladı",
        "packages.repair_engine.proposal_ready":    "📋 PR Önerisi Hazır — İnsan Onayı Gerekiyor",
        "packages.repair_engine.proposal_approved": "✅ PR Onaylandı",
        "packages.repair_engine.proposal_rejected": "❌ PR Reddedildi",
        "packages.repair_engine.canary_failed":     "🐦 Canary Doğrulama Başarısız",
        "packages.repair_engine.duplicate_incident":"🔍 Tekrar Eden Incident",
        "packages.repair_engine.manual_escalation": "🔔 Manuel İnceleme Gerekiyor",
        "provider.quarantined":     "📉 Sağlayıcı Karantinaya Alındı",
        "provider.recovered":       "📈 Sağlayıcı İyileşti",
        "system.metabolism.pacing": "🐢 Metabolizma Yavaşlatıldı (ECO)",
        "system.metabolism.blackout": "🌑 Metabolik Kararma (Emergency)",
    }

    def __init__(self):
        self._bot_token = BOT_TOKEN
        self._recipients = RECIPIENTS

    async def notify_event(self, event_type: str, payload: dict):
        title = self.NOTIFY_EVENTS.get(event_type)
        if not title:
            title = f"Sistem Olayı: {event_type}"

        msg = f"🔔 *{title}*\n\n"

        # General fields
        if payload.get("title"):
            msg += f"📌 {payload['title']}\n"
        if payload.get("message"):
            msg += f"💬 {payload['message'][:500]}\n"
        if payload.get("duration_s"):
            msg += f"⏳ Süre: {payload['duration_s']}s\n"

        # Repair/Incident-specific fields
        if payload.get("incident_id"):
            msg += f"🆔 Incident: `{payload['incident_id'][:14]}`\n"
        if payload.get("module"):
            msg += f"📦 Modül: `{payload['module']}`\n"
        if payload.get("symptom"):
            msg += f"⚠️ Semptom: {str(payload['symptom'])[:150]}\n"
        if payload.get("severity"):
            msg += f"🎯 Önem: *{payload['severity'].upper()}*\n"
        if payload.get("job_id"):
            msg += f"⚙️ Job: `{payload['job_id'][:14]}`\n"
        if payload.get("pr_id"):
            msg += f"📋 PR: `{payload['pr_id'][:14]}`\n"
        if payload.get("risk"):
            emoji = "🔴" if payload["risk"] == "high" else ("🟡" if payload["risk"] == "medium" else "🟢")
            msg += f"{emoji} Risk: *{payload['risk'].upper()}*\n"
        if payload.get("validation_summary"):
            msg += f"🧪 Validation: {payload['validation_summary']}\n"

        # Provider fields
        if payload.get("provider"):
            msg += f"🤖 Sağlayıcı: `{payload['provider']}`\n"
        if payload.get("reason"):
            msg += f"❗ Neden: {payload['reason'][:100]}\n"

        reply_markup = None
        
        # Add approval buttons if needed
        request_id = payload.get("request_id") or payload.get("pr_id")
        if event_type in ("approval.needed", "packages.repair_engine.proposal_ready") and request_id:
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "✅ Onayla", "callback_data": f"approve:{request_id}"},
                    {"text": "❌ Reddet", "callback_data": f"reject:{request_id}"}
                ]]
            }

        await self._send_to_all(msg, reply_markup=reply_markup)

    async def _send_to_all(self, text: str, reply_markup: Optional[dict] = None):
        if not self._bot_token or not self._recipients:
            logger.warning("Telegram Bot Token or Recipients not set.")
            return
        
        async with httpx.AsyncClient(timeout=10) as client:
            for chat_id in self._recipients:
                try:
                    payload = {
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    }
                    if reply_markup:
                        payload["reply_markup"] = reply_markup
                        
                    resp = await client.post(
                        f"https://api.telegram.org/bot{self._bot_token}/sendMessage",
                        json=payload,
                    )
                    if resp.status_code != 200:
                        logger.warning(f"Telegram returned non-200 status code: {resp.status_code} - {resp.text}. Retrying plain text.")
                        payload.pop("parse_mode", None)
                        retry_resp = await client.post(
                            f"https://api.telegram.org/bot{self._bot_token}/sendMessage",
                            json=payload,
                        )
                        if retry_resp.status_code != 200:
                            logger.warning(f"Telegram retry plain text also failed: {retry_resp.status_code} - {retry_resp.text}")
                except Exception as e:
                    logger.warning(f"Failed to send Telegram message to {chat_id}: {e}")

    async def send_to_chat(self, chat_id: int, text: str, reply_markup: Optional[dict] = None) -> bool:
        if not self._bot_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup

                resp = await client.post(
                    f"https://api.telegram.org/bot{self._bot_token}/sendMessage",
                    json=payload,
                )
                if resp.status_code == 200:
                    return True
                
                logger.warning(f"Telegram send_to_chat returned non-200: {resp.status_code} - {resp.text}. Retrying plain text.")
                payload.pop("parse_mode", None)
                retry_resp = await client.post(
                    f"https://api.telegram.org/bot{self._bot_token}/sendMessage",
                    json=payload,
                )
                return retry_resp.status_code == 200
        except Exception as e:
            logger.warning(f"Telegram send_to_chat failed: {e}")
            return False

telegram_notifier = TelegramNotifier()
