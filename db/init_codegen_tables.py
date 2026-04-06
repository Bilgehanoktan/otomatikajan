import asyncio
import os
import sys

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def init_tables():
    print("--- [FAZ 12.1: VERİTABANI ŞEMA GÜNCELLEME] ---")
    try:
        from packages.persistence.session import init_db, verify_db_connection
        
        print("DB bağlantısı kontrol ediliyor...")
        if await verify_db_connection():
            print("DB Bağlantısı: OK")
        else:
            print("DB Bağlantısı: BAŞARISIZ")
            # SQLite fallback denenecek init_db içinde
            
        print("Tablolar oluşturuluyor...")
        await init_db()
        print("[BAŞARILI] Yeni tablolar (sovereign_code_results, sovereign_code_files) hazır.")
        
    except Exception as e:
        print(f"[HATA] Tablo oluşturma sırasında hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(init_tables())
