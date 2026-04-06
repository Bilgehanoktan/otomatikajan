import asyncio
import logging
import uuid
import sys
import os

# Import yolunu ayarla
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.packages.observability.logging import get_logger, configure_logging
from packages.persistence.session import AsyncSessionLocal
from sqlalchemy import select
from packages.persistence.models import DomainEventLog

async def verify():
    print("--- Logging Verification Starting ---")
    
    # 1. Konfigürasyon
    configure_logging()
    test_logger = get_logger("test_verification", force_db=True)
    
    # 2. Test Logu Gönder
    unique_msg = f"VERIFICATION_TEST_{uuid.uuid4().hex[:8]}"
    print(f"Sending log: {unique_msg}")
    test_logger.error(unique_msg)
    
    # 3. Kısa bir süre bekle (async task'ın tamamlanması için)
    print("Waiting for DB write...")
    await asyncio.sleep(2)
    
    # 4. DB'den Kontrol Et
    async with AsyncSessionLocal() as db:
        result = await packages.persistence.execute(
            select(DomainEventLog).where(DomainEventLog.message == unique_msg)
        )
        row = result.scalar_one_or_none()
        
        if row:
            print("✅ SUCCESS: Log found in database!")
            print(f"   ID: {row.id}")
            print(f"   Severity: {row.severity}")
            print(f"   Timestamp: {row.created_at}")
        else:
            print("❌ FAILURE: Log NOT found in database.")
            
    print("--- Verification Finished ---")

if __name__ == "__main__":
    asyncio.run(verify())
