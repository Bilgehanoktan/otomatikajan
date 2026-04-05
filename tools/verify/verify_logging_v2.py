import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import asyncio
import logging
import uuid
import sys

# Import yolunu ayarla
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from packages.observability.logging import get_logger, configure_logging
    from packages.persistence.session import AsyncSessionLocal
    from sqlalchemy import select
    from packages.persistence.models import DomainEventLog
except ImportError as e:
    print(f"Hata: Modüller yüklenemedi: {e}")
    sys.exit(1)

async def verify():
    print("--- Loglama Doğrulaması Başlıyor ---")
    
    # 1. Konfigürasyon
    try:
        configure_logging()
        # force_db=True ile DBLogHandler'ın eklendiğinden emin oluyoruz
        test_logger = get_logger("test_verification", force_db=True)
    except Exception as e:
        print(f"Konfigürasyon hatası: {e}")
        return

    # 2. Test Logu Gönder
    unique_msg = f"DOĞRULAMA_TESTİ_{uuid.uuid4().hex[:8]}"
    print(f"Log gönderiliyor: {unique_msg}")
    test_logger.error(unique_msg)
    
    # 3. Bekle (Async task'ın yazması için)
    print("Veritabanına yazılması için bekleniyor...")
    await asyncio.sleep(3)
    
    # 4. DB'den Kontrol Et
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DomainEventLog).where(DomainEventLog.message == unique_msg)
            )
            row = result.scalar_one_or_none()
            
            if row:
                print("✅ BAŞARILI: Log veritabanında bulundu!")
                print(f"   ID: {row.id}")
                print(f"   Severity: {row.severity}")
                print(f"   Event Type: {row.event_type}")
            else:
                print("❌ HATA: Log veritabanına düşmedi.")
    except Exception as e:
        print(f"Veritabanı okuma hatası: {e}")
            
    print("--- Doğrulama Tamamlandı ---")

if __name__ == "__main__":
    asyncio.run(verify())
