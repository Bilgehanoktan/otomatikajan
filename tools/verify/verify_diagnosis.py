
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

# .env dosyasını zorla yükle
load_dotenv(".env", override=True)

async def test_conn():
    db_url = os.getenv("DATABASE_URL")
    print(f"Test ediliyor: {db_url}")
    try:
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"BAŞARILI: {result.scalar()}")
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
