import asyncio
import os
import uuid
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from packages.persistence.session import AsyncSessionLocal
from sqlalchemy import text

async def peek():
    print("🚀 Veritabanı Gözetleme...")
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id, status, title FROM ceo_suggested_tasks LIMIT 5"))
        rows = res.fetchall()
        print(f"📦 Bulunan satır sayısı (limit 5): {len(rows)}")
        for r in rows:
            print(f"ID: {r[0]}, Durum: '{r[1]}', Başlık: {r[2]}")
        
        # Suggested sayısını tekrar say
        res_sug = await db.execute(text("SELECT count(*) FROM ceo_suggested_tasks WHERE status = 'suggested'"))
        count = res_sug.scalar()
        print(f"🔍 'suggested' durumundaki tam sayı: {count}")

if __name__ == "__main__":
    asyncio.run(peek())
