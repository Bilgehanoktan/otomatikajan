import os
import logging
import httpx
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from apps.bilgeapi.security.secret_scanner import SecretScanner

logger = logging.getLogger("bilgeapi.integrations.telegram")

class TelegramBridge:
    def __init__(self, secret_scanner: Optional[SecretScanner] = None):
        self.bot_token = os.getenv("BILGEAPI_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        # chat_id fallback chain: BILGEAPI_TELEGRAM_CHAT_ID -> TELEGRAM_CHAT_ID -> TELEGRAM_ADMIN_IDS -> TELEGRAM_ALLOWED_IDS
        raw_chat_id = (
            os.getenv("BILGEAPI_TELEGRAM_CHAT_ID") or 
            os.getenv("TELEGRAM_CHAT_ID") or 
            os.getenv("TELEGRAM_ADMIN_IDS") or 
            os.getenv("TELEGRAM_ALLOWED_IDS", "")
        )
        self.chat_id = [cid.strip() for cid in raw_chat_id.split(",") if cid.strip()][0] if raw_chat_id else ""
        
        self.secret_token = os.getenv("BILGEAPI_TELEGRAM_WEBHOOK_SECRET") or os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
        self.secret_scanner = secret_scanner or SecretScanner()

    def _is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def send_notification(self, message: str) -> bool:
        """
        Sends a standard text notification to the configured chat_id.
        Applies secret masking before sending.
        """
        clean_msg = self.secret_scanner.scan_and_mask(message)
        
        if not self._is_configured():
            logger.info(f"[MOCK TELEGRAM NOTIFICATION] Chat ID {self.chat_id}: {clean_msg}")
            return True

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": clean_msg,
            "parse_mode": "HTML"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    async def send_approval_request(
        self,
        approval_id: str,
        title: str,
        description: str,
        token: str,
        risk_level: str,
        risk_score: float,
        reasons: List[str],
        action_hash: str,
        expiration_minutes: int = 15
    ) -> bool:
        """
        Sends a structured approval request with inline keyboard buttons.
        """
        # Expiration calculation
        exp_time = (datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)).strftime("%H:%M:%S UTC")
        
        # 1. Format clean text (Secret masking applied)
        masked_title = self.secret_scanner.scan_and_mask(title)
        masked_desc = self.secret_scanner.scan_and_mask(description)
        masked_reasons = [self.secret_scanner.scan_and_mask(r) for r in reasons]
        
        reasons_bullets = "\n".join(f"• {r}" for r in masked_reasons)
        
        message_text = (
            f"⚠️ <b>Approval Required: {masked_title}</b>\n\n"
            f"📝 <b>Description:</b> {masked_desc}\n"
            f"⚖️ <b>Risk Level:</b> {risk_level} (Score: {risk_score:.1f}/10)\n\n"
            f"🔍 <b>Reasons:</b>\n{reasons_bullets}\n\n"
            f"🔑 <b>Action Hash:</b> <code>{action_hash}</code>\n"
            f"⏳ <b>Expires At:</b> {exp_time} ({expiration_minutes} mins)\n"
        )
        
        # 2. Compact callback_data constraints (first 8 chars of token)
        short_token = token[:8]
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve", "callback_data": f"approve:{approval_id}:{short_token}"},
                    {"text": "❌ Reject", "callback_data": f"reject:{approval_id}:{short_token}"}
                ]
            ]
        }
        
        if not self._is_configured():
            logger.info(
                f"[MOCK TELEGRAM APPROVAL REQUEST]\n"
                f"Text: {message_text}\n"
                f"Keyboard: {inline_keyboard}"
            )
            return True

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message_text,
            "parse_mode": "HTML",
            "reply_markup": inline_keyboard
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram approval request: {e}")
            return False
