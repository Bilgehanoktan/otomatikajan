"""
Telegram Bot Polling Mode — Faz 4
Yerel geliştirme ve test için botu polling (sorgulama) modunda çalıştırır.
Webhook gerektirmez.

Kullanım: python telegram/polling.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Proje kök dizinini sys.path'e ekle (modül importları için)
root_dir = str(Path(__file__).parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from dotenv import load_dotenv
if os.path.exists(".env"):
    load_dotenv(".env", override=True)
if os.path.exists(".env.local"):
    load_dotenv(".env.local", override=True)

from telegram_app.bot import handle_update, BOT_TOKEN, _tg_available
from observability.logging import get_logger

logger = get_logger("telegram.polling")

if not _tg_available():
    logger.error("python-telegram-bot kütüphanesi kurulu değil!")
    sys.exit(1)

if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN ayarlanmamış! .env dosyasını kontrol edin.")
    sys.exit(1)

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import time

async def heartbeat_loop():
    try:
        from db.session import get_redis_client
        redis = get_redis_client()
        while True:
            if redis is not None:
                await redis.set("faz12:telegram_heartbeat", str(int(time.time())), ex=30)
            await asyncio.sleep(15)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Heartbeat loop error: {e}")

async def generic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm mesajları ve buton tıklamalarını bot.py'deki handle_update mantığına iletir."""
    # Callback query ise ona göre işle
    is_callback = bool(update.callback_query)
    
    if not update.message and not update.edited_message and not is_callback:
        return

    # Update nesnesini dict'e çevir (bot.py'deki handle_update dict bekliyor)
    update_dict = update.to_dict()
    
    try:
        # bot.py'deki ana işleyiciyi çağır
        result = await handle_update(update_dict)
        
        if result:
            chat_id, response_text, reply_markup = result
            
            # Yanıtı gönder
            kwargs = {
                "chat_id": chat_id,
                "text": response_text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            if reply_markup:
                # python-telegram-bot InlineKeyboardMarkup nesnesi bekler, 
                # ama biz dict yolluyoruz. telegram.InlineKeyboardMarkup'a çevirmeliyiz.
                from telegram import InlineKeyboardMarkup
                kwargs["reply_markup"] = InlineKeyboardMarkup.de_json(reply_markup, None)

            await context.bot.send_message(**kwargs)

        # Buton tıklandığında Telegram'daki spinner'ı durdur
        if is_callback and update.callback_query:
            await update.callback_query.answer()

    except Exception as e:
        logger.error(f"Polling işleme hatası: {e}", exc_info=True)


async def main():
    logger.info("Telegram Bot Polling başlatılıyor...")
    
    # Application oluştur
    application = Application.builder().token(BOT_TOKEN).build()

    # Tüm mesajlar ve komutlar için tek bir handler
    # handle_update zaten komutları (/start vs) kendi içinde parse ediyor
    application.add_handler(MessageHandler(filters.ALL, generic_handler))

    logger.info("Bot aktif. Durdurmak için Ctrl+C.")
    
    # Başlat ve bekle
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    hb_task = asyncio.create_task(heartbeat_loop())
    
    # Çalışmaya devam et
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Bot durduruluyor...")
        hb_task.cancel()
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
