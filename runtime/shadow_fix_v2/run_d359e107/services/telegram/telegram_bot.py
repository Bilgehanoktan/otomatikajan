import asyncio
import logging
import os
import sys
import httpx
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Align python path to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Logging Setup
log_file = os.path.join(PROJECT_ROOT, "runtime", "logs", "telegram_bot.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SovereignAGI-TelegramBot")

# Global Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = "http://127.0.0.1:8000"

def is_authorized(user_id: int) -> bool:
    """Verifies if the Telegram User ID is authorized as allowed/admin in .env."""
    allowed_str = os.getenv("TELEGRAM_ALLOWED_IDS", "")
    admin_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
    allowed_ids = [int(x.strip()) for x in (allowed_str + "," + admin_str).split(",") if x.strip().isdigit()]
    # Fallback to allow if list is empty for safe bootstrap, otherwise enforce strict check
    if not allowed_ids:
        return True
    return user_id in allowed_ids

# --- Commands ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the operator and renders the control panel options."""
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text("❌ Yetkisiz Erişim! Bu mobil kontrol botu sadece yetkilendirilmiş sistem operatörlerine açıktır.")
        return

    logger.info("Admin authorized session started for user_id=%s (%s)", user.id, user.username)

    welcome_text = (
        f"⚡ **Sovereign AGI Mobile Control Hub** ⚡\n\n"
        f"Hoş geldiniz Operatör **{user.first_name}**!\n"
        f"Bu güvenli kanal üzerinden sistem telemetrilerini izleyebilir, veritabanını kendi kendine "
        f"iyileştirebilir ve otonom tamir görevlerini başlatabilirsiniz.\n\n"
        f"Lütfen yapmak istediğiniz işlemi seçin:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📊 Sistem Durumu", callback_data="status_check"),
            InlineKeyboardButton("🗄️ Veritabanı Teşhis", callback_data="db_check")
        ],
        [
            InlineKeyboardButton("🔧 UI Onarım İşleri", callback_data="ui_repair_list"),
            InlineKeyboardButton("♻️ DB Kendi Kendine İyileştirme", callback_data="db_repair_confirm")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /durum or /status."""
    user = update.effective_user
    if not is_authorized(user.id): return
    
    await update.message.reply_chat_action("typing")
    status_text = await get_status_report()
    await update.message.reply_text(status_text, parse_mode="Markdown")

async def db_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /db."""
    user = update.effective_user
    if not is_authorized(user.id): return
    
    await update.message.reply_chat_action("typing")
    db_text = await get_db_report()
    await update.message.reply_text(db_text, parse_mode="Markdown")

async def repair_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /repair."""
    user = update.effective_user
    if not is_authorized(user.id): return
    
    await update.message.reply_chat_action("typing")
    await send_ui_repair_list(update)

# --- Helper Integration Methods ---

async def get_status_report() -> str:
    """Probes ports 8000 and 3100 to format a high-fidelity Turkish status report."""
    backend_ok = False
    frontend_ok = False
    
    # 1. Backend Probe
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{BACKEND_URL}/health")
            if r.status_code == 200:
                backend_ok = True
    except Exception:
        pass
        
    # 2. Frontend Probe
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://127.0.0.1:3100")
            if r.status_code == 200:
                frontend_ok = True
    except Exception:
        pass
        
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = (
        f"📊 **Sovereign AGI Sistem Telemetri Raporu**\n"
        f"📅 _Zaman:_ `{time_str}`\n\n"
        f"🖥️ **Süreç Durumları:**\n"
        f"  - **API Gateway (Port 8000):** { '🟢 AKTİF (Online)' if backend_ok else '🔴 ÇEVRİMDIŞI (Offline)' }\n"
        f"  - **Control Plane UI (Port 3100):** { '🟢 AKTİF (Online)' if frontend_ok else '🔴 ÇEVRİMDIŞI (Offline)' }\n\n"
        f"🛡️ **Genel Sağlık Skoru:** { '🟢 %100 KARARLI' if (backend_ok and frontend_ok) else '🟡 KISMİ ERİŞİM / DEGRADED' if (backend_ok or frontend_ok) else '🔴 KRİTİK ÇÖKÜŞ' }\n\n"
        f"💡 _Öneri:_ Sistem izleme ve koruma kalkanları (Watchdog) arka planda aktiftir ve çökmelerde servisleri 30 saniye içinde otomatik kurtarır."
    )
    return report

async def get_db_report() -> str:
    """Directly queries DatabaseRecoveryManager to inspect fallback DB health."""
    from services.database.recovery.manager import DatabaseRecoveryManager
    try:
        diag = DatabaseRecoveryManager.diagnose()
        if not diag["exists"]:
            return "❌ **Veritabanı Bulunamadı!** Local fallback veritabanı dosyası diskte yer almıyor."
            
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        table_summary = ""
        # Show top 5 tables with most rows
        sorted_tables = sorted(diag["tables"].items(), key=lambda item: item[1]["rows"], reverse=True)[:5]
        for t_name, info in sorted_tables:
            table_summary += f"  - `{t_name}`: {info['rows']} satır\n"
            
        report = (
            f"🗄️ **SQLite Veritabanı Teşhis Raporu**\n"
            f"📅 _Zaman:_ `{time_str}`\n\n"
            f"📂 **Dosya:** `{os.path.basename(diag['database_path'])}`\n"
            f"⚖️ **Boyut:** `{round(diag['size_bytes'] / 1024, 1)} KB`\n"
            f"🔒 **Bütünlük (Integrity Check):** { '🟢 OK (Sağlıklı)' if diag['integrity_check'] == 'OK' else '🔴 HATA - BOZULMA' }\n"
            f"🏷️ **Durum Etiketi:** `🟢 {diag['status']}`\n\n"
            f"📈 **En Yoğun Tablolar (Top 5):**\n{table_summary}\n"
            f"💡 Toplam {len(diag['tables'])} şema tablosu başarıyla tarandı."
        )
        return report
    except Exception as e:
        return f"❌ **Teşhis Başarısız Oldu:** {str(e)}"

async def send_ui_repair_list(update: Update):
    """Lists detected UI repair cases needing operator approvals/actions."""
    from libs.db.session import AsyncSessionLocal
    from sqlalchemy import select
    from libs.db.models.ui_repair_models import UIRepairCase
    
    async with AsyncSessionLocal() as db:
        try:
            stmt = select(UIRepairCase).where(UIRepairCase.status == "DETECTED").limit(3)
            res = await db.execute(stmt)
            cases = res.scalars().all()
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Veritabanı sorgusu başarısız oldu: {e}")
            return

    if not cases:
        await update.effective_message.reply_text("🟢 **Bekleyen UI Onarım İşi Yok!** Sistemdeki tüm arayüz rotaları ve bileşenleri sağlıklı durumdadır.")
        return

    await update.effective_message.reply_text("🔧 **Bekleyen UI Onarım ve Tamir Görevleri (Top 3):**")

    for case in cases:
        case_info = (
            f"🆔 **Case ID:** `{str(case.id)[:8]}`\n"
            f"📍 **Rota:** `{case.route}`\n"
            f"🔥 **Hata Tipi:** `{case.failure_type}`\n"
            f"⚠️ **Öncelik:** `{case.severity}`\n"
            f"📅 **Tespit Tarihi:** `{case.created_at.strftime('%Y-%m-%d %H:%M') if case.created_at else 'N/A'}`"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🛠️ Otonom Onarımı Tetikle", callback_data=f"launch_repair_{case.id}"),
                InlineKeyboardButton("✅ Çözüldü İşaretle", callback_data=f"mark_resolved_{case.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(case_info, reply_markup=reply_markup)

# --- Button Callback Handler ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes inline keyboard callback triggers asynchronously."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    if not is_authorized(user.id): return

    data = query.data
    logger.info("Button clicked: data=%s by user_id=%s", data, user.id)

    if data == "status_check":
        status_text = await get_status_report()
        await query.message.reply_text(status_text, parse_mode="Markdown")
        
    elif data == "db_check":
        db_text = await get_db_report()
        await query.message.reply_text(db_text, parse_mode="Markdown")
        
    elif data == "ui_repair_list":
        await send_ui_repair_list(update)
        
    elif data == "db_repair_confirm":
        confirm_text = (
            "⚠️ **DİKKAT: Veritabanı Kendi Kendine İyileştirme (Rebuild)**\n\n"
            "Bu işlem yerel veritabanı şemasındaki tüm tabloları drop edip "
            "iterdump SQL üzerinden sıfırdan ve optimize edilmiş olarak inşa edecektir. "
            "Süreç öncesinde anlık bir veritabanı yedeği otomatik alınacaktır.\n\n"
            "Devam etmek istiyor musunuz?"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Evet, İnşa Et!", callback_data="db_repair_execute"),
                InlineKeyboardButton("❌ İptal", callback_data="db_repair_cancel")
            ]
        ]
        await query.message.reply_text(confirm_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data == "db_repair_cancel":
        await query.message.reply_text("❌ İşlem operatör tarafından iptal edildi.")
        
    elif data == "db_repair_execute":
        await query.message.reply_text("♻️ Veritabanı yedekleniyor ve in-place tamir süreci başlatılıyor...")
        from services.database.recovery.manager import DatabaseRecoveryManager
        try:
            res = DatabaseRecoveryManager.recover()
            if res["status"] == "SUCCESS":
                success_msg = (
                    f"✅ **Veritabanı İyileştirme Başarılı!**\n\n"
                    f"📝 _Mesaj:_ {res['message']}\n"
                    f"📦 _Yedek Dosyası:_ `{os.path.basename(res['backup_path'])}`"
                )
                await query.message.reply_text(success_msg, parse_mode="Markdown")
            else:
                await query.message.reply_text(f"❌ **İyileştirme Başarısız Oldu:** {res['message']}")
        except Exception as ex:
            await query.message.reply_text(f"❌ **Kurtarma Esnasında Hata:** {ex}")
            
    elif data.startswith("launch_repair_"):
        case_id = data.replace("launch_repair_", "")
        await query.message.reply_text(f"⚙️ `Case {case_id[:8]}` için otonom tamir motoruna hand-off yapılıyor...")
        
        # Trigger the UI Repair endpoint asynchronously
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(f"{BACKEND_URL}/api/v1/ui-repair/cases/{case_id}/repair")
                if r.status_code == 200:
                    await query.message.reply_text(f"✅ `Case {case_id[:8]}` için otonom tamir süreci başarıyla tetiklendi!")
                else:
                    await query.message.reply_text(f"❌ **Tetikleme Başarısız:** HTTP {r.status_code} - {r.text}")
        except Exception as e:
            await query.message.reply_text(f"❌ **API Bağlantı Hatası:** {e}")
            
    elif data.startswith("mark_resolved_"):
        case_id = data.replace("mark_resolved_", "")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(f"{BACKEND_URL}/api/v1/ui-repair/cases/{case_id}/resolve")
                if r.status_code == 200:
                    await query.message.reply_text(f"✅ `Case {case_id[:8]}` başarıyla manuel çözüldü (RESOLVED) olarak işaretlendi.")
                else:
                    await query.message.reply_text(f"❌ **Girişim Başarısız:** HTTP {r.status_code}")
        except Exception as e:
            await query.message.reply_text(f"❌ **API Bağlantı Hatası:** {e}")

# --- Text Handler for fallback ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_authorized(user.id): return
    await update.message.reply_text("💡 Lütfen kontrol paneli seçeneklerini görmek için /start komutunu gönderin.")

# --- Main Entry Point ---

def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not defined in .env!")
        sys.exit(1)

    # Initialize python-telegram-bot application
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("durum", status_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("db", db_command))
    app.add_handler(CommandHandler("repair", repair_command))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set up asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_bot():
        async with app:
            await app.start()
            # drop_pending_updates=True avoids spamming the operator with old offline updates
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
            logger.info("SovereignAGI-TelegramBot polling successfully initiated.")
            await asyncio.Event().wait()

    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot execution interrupted by operator.")
    except Exception as exc:
        logger.error("Global exception in bot execution: %s", exc)

if __name__ == "__main__":
    main()
