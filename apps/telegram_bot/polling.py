import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Load environment
load_dotenv()

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_IDS = os.getenv("TELEGRAM_ALLOWED_IDS", "").split(",")
ADMIN_IDS = os.getenv("TELEGRAM_ADMIN_IDS", "").split(",")

async def check_auth(update: Update):
    user_id = str(update.effective_user.id)
    if ALLOWED_IDS and user_id not in ALLOWED_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Yetkisiz erişim. Lütfen sistem yöneticisi ile iletişime geçin.")
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
    
    # Placeholder for AGI Logic Integration
    # TODO: Connect to Sovereign Planner or Workflow API
    await update.message.reply_text(
        "🔄 **Mesaj Alındı.**\n"
        "Sovereign AGI çekirdeği şu an bu veriyi işliyor...",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    # TODO: Integrate with real health checks
    await update.message.reply_text(
        "📊 **Sistem Durumu:** [HEALTHY]\n"
        "✅ Core: Online\n"
        "✅ Workflow Engine: Online\n"
        "✅ LLM Orchestrator: Online",
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    logger.info("Sovereign AGI Telegram Bot starting...")
    app.run_polling()
