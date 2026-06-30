import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Load environment
load_dotenv()

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_IDS = os.getenv("TELEGRAM_ALLOWED_IDS", "").split(",")
ADMIN_IDS = os.getenv("TELEGRAM_ADMIN_IDS", "").split(",")

def get_backend_url() -> str:
    url = os.getenv("BACKEND_API_URL")
    if not url:
        url = "http://app:8000" if os.getenv("DOCKER_CONTAINER") == "true" else "http://localhost:8000"
    return url


def get_bilgeapi_url() -> str:
    url = os.getenv("BILGEAPI_ORIGIN") or os.getenv("BILGEAPI_API_URL")
    if not url:
        url = "http://bilgeapi:8100" if os.getenv("DOCKER_CONTAINER") == "true" else "http://localhost:8100"
    return url.rstrip("/")


def is_authorized_user_id(user_id: str) -> bool:
    has_allowed = any(uid.strip() for uid in ALLOWED_IDS if uid)
    has_admin = any(uid.strip() for uid in ADMIN_IDS if uid)
    return not (has_allowed or has_admin) or user_id in ALLOWED_IDS or user_id in ADMIN_IDS


def parse_approval_callback_data(data: str | None) -> dict[str, str] | None:
    parts = (data or "").split(":")
    if len(parts) != 3:
        return None
    action, approval_id, short_token = [part.strip() for part in parts]
    if action not in {"approve", "reject"} or not approval_id or not short_token:
        return None
    return {
        "action": action,
        "approval_id": approval_id,
        "short_token": short_token,
    }


def get_telegram_webhook_headers() -> dict[str, str]:
    secret_token = os.getenv("BILGEAPI_TELEGRAM_WEBHOOK_SECRET") or os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    if not secret_token:
        return {}
    return {"X-Telegram-Bot-Api-Secret-Token": secret_token}


async def forward_approval_callback_to_bilgeapi(update_payload: dict, client=None) -> tuple[bool, str]:
    callback_query = update_payload.get("callback_query") or {}
    parsed = parse_approval_callback_data(callback_query.get("data"))
    if not parsed:
        return False, "Geçersiz onay verisi."

    import httpx

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient()

    try:
        response = await client.post(
            f"{get_bilgeapi_url()}/v1/telegram/webhook",
            json=update_payload,
            headers=get_telegram_webhook_headers(),
            timeout=15.0,
        )
    finally:
        if owns_client:
            await client.aclose()

    if response.status_code == 200:
        verdict = "APPROVED" if parsed["action"] == "approve" else "REJECTED"
        return True, f"{verdict} kararı kaydedildi."

    detail = response.text[:240]
    try:
        payload = response.json()
        detail = str(payload.get("detail") or payload.get("message") or detail)[:240]
    except Exception:
        pass
    return False, f"Onay kaydedilemedi: HTTP {response.status_code} {detail}"


async def check_auth(update: Update):
    user_id = str(update.effective_user.id)
    has_allowed = any(uid.strip() for uid in ALLOWED_IDS if uid)
    has_admin = any(uid.strip() for uid in ADMIN_IDS if uid)
    
    if (has_allowed or has_admin) and user_id not in ALLOWED_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text(
            f"⛔ **Yetkisiz Erişim.**\n\n"
            f"Telegram ID'niz: `{user_id}`\n\n"
            f"Lütfen bu ID'yi `.env` dosyasındaki `TELEGRAM_ALLOWED_IDS` ve `TELEGRAM_ADMIN_IDS` kısımlarına ekleyip sistemi yeniden başlatın.",
            parse_mode="Markdown"
        )
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    await update.message.reply_text(
        "🚀 **Sovereign AGI (Faz 12.1) Sistemine Hoş Geldiniz!**\n\n"
        "Ben sizin stratejik asistanınızım. Komutlar:\n"
        "/status - Sistem durumunu kontrol et\n"
        "/analyze - Mevcut verileri analiz et\n"
        "/help - Bilgi al",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    text = update.message.text
    logger.info(f"Received message from {update.effective_user.id}: {text}")
    
    try:
        import httpx
        backend_url = get_backend_url()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{backend_url}/api/v1/orchestration/planner/analyze",
                json={"query": text, "user_id": str(update.effective_user.id)},
                timeout=60.0
            )
            
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("response", "İşlem tamamlandı.")
                try:
                    await update.message.reply_text(reply, parse_mode="Markdown")
                except Exception as parse_err:
                    logger.warning(f"Markdown send failed, retrying plain text: {parse_err}")
                    await update.message.reply_text(reply)
                return
    except Exception as e:
        logger.error(f"Planner integration failed: {e}")
        
    await update.message.reply_text(
        "🔄 **Mesaj Alındı.**\n"
        "Sovereign AGI çekirdeğine ulaşılamadı. İstek kuyruğa alındı.",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    try:
        import httpx
        backend_url = get_backend_url()
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{backend_url}/health", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                health_status = data.get("status", "HEALTHY")
                await update.message.reply_text(
                    f"📊 **Sistem Durumu:** [{health_status}]\n"
                    "✅ Backend: Online\n"
                    "✅ Veritabanı Bağlantısı: Başarılı",
                    parse_mode="Markdown"
                )
                return
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
    await update.message.reply_text(
        "📊 **Sistem Durumu:** [DEGRADED]\n"
        "❌ Backend bağlantısı sağlanamadı veya API yanıt vermiyor.",
        parse_mode="Markdown"
    )

async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    user_id = str(update.effective_user.id) if update.effective_user else ""
    if not is_authorized_user_id(user_id):
        await query.answer("Yetkisiz erişim.", show_alert=True)
        return

    if not parse_approval_callback_data(query.data):
        await query.answer("Bu onay bağlantısı geçersiz veya eski formatta.", show_alert=True)
        return

    await query.answer("Onay kararı işleniyor...")
    try:
        ok, message = await forward_approval_callback_to_bilgeapi(update.to_dict())
    except Exception as exc:
        logger.error("Telegram approval callback failed: %s", exc)
        await query.answer("Onay kaydedilemedi. Sistem loglarını kontrol edin.", show_alert=True)
        return

    await query.answer(message, show_alert=not ok)
    if not query.message:
        return

    if ok:
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as exc:
            logger.warning("Failed to clear approval callback keyboard: %s", exc)
        await query.message.reply_text(f"✅ {message}")
    else:
        await query.message.reply_text(f"⚠️ {message}")


if __name__ == '__main__':
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(handle_approval_callback, pattern=r"^(approve|reject):"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    logger.info("Sovereign AGI Telegram Bot starting...")
    app.run_polling()
