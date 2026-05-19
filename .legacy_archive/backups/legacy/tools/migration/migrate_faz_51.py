import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import DATABASE_URL

async def migrate_phase_51():
    print(f"BİLİŞSEL EVRİM: Veritabanı Şeması Güncelleniyor (Faz 51)...")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # parent_id ekle
        try:
            await conn.execute(text("ALTER TABLE subtasks ADD COLUMN parent_id UUID REFERENCES subtasks(id) ON DELETE SET NULL"))
            print("[+] parent_id kolonu eklendi.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("[!] parent_id zaten var.")
            else:
                print(f"[-] parent_id hatası: {e}")

        # dependencies ekle
        try:
            await conn.execute(text("ALTER TABLE subtasks ADD COLUMN dependencies JSONB DEFAULT '[]'"))
            print("[+] dependencies kolonu eklendi.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("[!] dependencies zaten var.")
            else:
                print(f"[-] dependencies hatası: {e}")

    await engine.dispose()
    print("BİLİŞSEL EVRİM: Şema günelleme tamamlandı.")

if __name__ == "__main__":
    asyncio.run(migrate_phase_51())
