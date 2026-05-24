import asyncio
import logging
import os
import signal
import sys
import threading
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

# Add current directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.db import init_db
import bot.state as state
from bot.services.webhook import start_webhook_server
from bot.handlers.commands import start, durum, ajanlar, gorevler, gelir, portfoy, rapor, n8n_status, yeni_talep, limitler, limit_sifirla, iptal, yardim
from bot.handlers.messages import handle_message, guvenlik
from bot.handlers.callbacks import button_callback

# Load environment variables
load_dotenv()

# Setup logging with Rotation
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_file = "logs/bot_local.log"
os.makedirs("logs", exist_ok=True)

rot_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
rot_handler.setFormatter(log_formatter)
rot_handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(rot_handler)

# Konsol çıktısı için de ekleyelim
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

# --- Resilience Mechanisms ---
LOCK_FILE = "bot.lock"
_lock_file_handle = None

def acquire_lock():
    global _lock_file_handle
    if os.name == "nt":
        try:
            if os.path.exists(LOCK_FILE):
                try:
                    os.remove(LOCK_FILE)
                except OSError:
                    print("HATA: Bot zaten calisiyor.")
                    sys.exit(1)
            _lock_file_handle = open(LOCK_FILE, "w")
            _lock_file_handle.write(str(os.getpid()))
            _lock_file_handle.flush()
            import msvcrt
            msvcrt.locking(_lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        except (IOError, AttributeError, ImportError):
            print("HATA: Bot kilitlenemedi. Zaten calisiyor olabilir.")
            sys.exit(1)
    else:
        try:
            import fcntl
            fp = open(LOCK_FILE, "w")
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (ImportError, OSError):
            # Fallback or allow if fcntl not available
            pass

def release_lock():
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass

def verify_db_schema():
    import sqlite3
    db_path = "backend/company.db"
    if not os.path.exists(db_path):
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(stats)")
        columns = [column[1] for column in cursor.fetchall()]
        required_columns = ["admin_id", "total_requests", "approved", "rejected", "total_revenue", "is_active"]
        missing = [col for col in required_columns if col not in columns]
        if missing:
            logger.warning(f"Database missing columns: {missing}")
            for col in missing:
                type_map = {"admin_id": "TEXT", "is_active": "BOOLEAN DEFAULT 0"}
                col_type = type_map.get(col, "INTEGER DEFAULT 0")
                cursor.execute(f"ALTER TABLE stats ADD COLUMN {col} {col_type}")
            conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB verification error: {e}")

def signal_handler(sig, frame):
    logger.info("Shutdown signal received, cleaning up...")
    release_lock()
    sys.exit(0)

def main():
    # 0. Startup checks
    acquire_lock()
    init_db()
    verify_db_schema()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 1. Load initial state from DB
    state.load_initial_state()

    # 2. Webhook server (separate thread, port 9090)
    webhook_thread = threading.Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()

    # 3. Telegram bot setup
    if not state.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)

    app = Application.builder().token(state.TELEGRAM_BOT_TOKEN).build()

    # Add Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("durum", durum))
    app.add_handler(CommandHandler("ajanlar", ajanlar))
    app.add_handler(CommandHandler("gorevler", gorevler))
    app.add_handler(CommandHandler("gelir", gelir))
    app.add_handler(CommandHandler("portfoy", portfoy))
    app.add_handler(CommandHandler("rapor", rapor))
    app.add_handler(CommandHandler("guvenlik", guvenlik))
    app.add_handler(CommandHandler("n8n", n8n_status))
    app.add_handler(CommandHandler("yenitalep", yeni_talep))
    app.add_handler(CommandHandler("limitler", limitler))
    app.add_handler(CommandHandler("limit_sifirla", limit_sifirla))
    app.add_handler(CommandHandler("iptal", iptal))
    app.add_handler(CommandHandler("yardim", yardim))

    # Add Callback & Message Handlers
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 4. Set up event loop for asynchronous tasks
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    state.event_loop = loop

    async def run_bot():
        async with app:
            await app.start()
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
            logger.info("Bot polling initiated")
            await asyncio.Event().wait()

    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        pass
    finally:
        release_lock()

if __name__ == "__main__":
    main()
