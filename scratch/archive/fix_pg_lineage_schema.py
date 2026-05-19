
import asyncio
from sqlalchemy import text
from libs.db.session import get_engine, is_db_degraded

async def fix_pg_schema():
    if is_db_degraded():
        print("Sistem zaten SQLite fallback modunda. Postgres'e ulaÅŸÄ±lamadÄ±ÄŸÄ± iÃ§in ÅŸema dÃ¼zeltilemiyor.")
        return

    engine = get_engine()
    if "sqlite" in str(engine.url):
        print("Engine SQLite olarak dÃ¶ndÃ¼. Postgres ÅŸemasÄ± dÃ¼zeltilemiyor.")
        return

    print(f"Postgres ÅŸemasÄ± kontrol ediliyor: {engine.url}")
    
    async with engine.begin() as conn:
        # 1. decision_lineage.outcome
        try:
            await conn.execute(text("ALTER TABLE decision_lineage ADD COLUMN outcome VARCHAR"))
            print("OK: 'decision_lineage.outcome' kolonu eklendi.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("INFO: 'decision_lineage.outcome' zaten mevcut.")
            else:
                print(f"ERROR: {e}")

        # 2. decision_lineage.confidence_score
        try:
            await conn.execute(text("ALTER TABLE decision_lineage ADD COLUMN confidence_score FLOAT DEFAULT 1.0"))
            print("OK: 'decision_lineage.confidence_score' kolonu eklendi.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("INFO: 'decision_lineage.confidence_score' zaten mevcut.")
            else:
                print(f"ERROR: {e}")

        # 3. decision_lineage.integrity_hash
        try:
            await conn.execute(text("ALTER TABLE decision_lineage ADD COLUMN integrity_hash VARCHAR(64)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_decision_lineage_integrity_hash ON decision_lineage(integrity_hash)"))
            print("OK: 'decision_lineage.integrity_hash' kolonu ve indeksi eklendi.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("INFO: 'decision_lineage.integrity_hash' zaten mevcut.")
            else:
                print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(fix_pg_schema())
