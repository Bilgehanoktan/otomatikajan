import sys
import os
from pathlib import Path

# Project root path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from libs.config import DATABASE_URL

def get_current_alembic_version(engine):
    """Veritabanındaki mevcut alembic sürümünü döner."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        print(f"HATA: Alembic sürümü okunamadı (Tablo yok mu?): {e}")
        return None

def verify_schema():
    print("--- Veritabani Sema Dogrulama ---")
    
    # Alembic konfigürasyonu
    ini_path = os.path.join(ROOT_DIR, "libs", "db", "migrations", "alembic.ini")
    if not os.path.exists(ini_path):
        # Üst dizinde de olabilir
        ini_path = os.path.join(ROOT_DIR, "alembic.ini")
        
    alembic_cfg = Config(ini_path)
    
    # Script dizini (versions klasörünün olduğu yer)
    # migrations_dir = os.path.join(ROOT_DIR, "libs", "db", "migrations")
    # alembic_cfg.set_main_option("script_location", migrations_dir)
    
    script = ScriptDirectory.from_config(alembic_cfg)
    head_revision = script.get_current_head()
    
    # Senkron engine kullan (Dogrulama icin yeterli)
    sync_url = DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    
    current_revision = get_current_alembic_version(engine)
    
    print(f"Beklenen (Head): {head_revision}")
    print(f"Mevcut (DB):   {current_revision}")
    
    if current_revision == head_revision:
        print("BASARILI: Veritabanı şeması güncel.")
        return True
    else:
        print("HATA: Veritabanı şeması GÜNCEL DEĞİL!")
        print("Lütfen 'alembic upgrade head' komutunu çalıştırın.")
        return False

if __name__ == "__main__":
    if not verify_schema():
        sys.exit(1)
    sys.exit(0)
