
import asyncio
import os
from sqlalchemy import text
from libs.db.session import get_engine

async def fix_schema():
    engine = get_engine()
    if "postgresql" not in str(engine.url):
        print("Not using PostgreSQL. Skipping schema fix.")
        return

    async with engine.begin() as conn:
        print("Checking decision_lineage table for missing columns...")
        
        # Add outcome if missing
        try:
            await conn.execute(text("ALTER TABLE decision_lineage ADD COLUMN outcome VARCHAR"))
            print("Added column 'outcome' to 'decision_lineage'")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("Column 'outcome' already exists.")
            else:
                print(f"Error adding 'outcome': {e}")

        # Add integrity_hash if missing
        try:
            await conn.execute(text("ALTER TABLE decision_lineage ADD COLUMN integrity_hash VARCHAR(64)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_decision_lineage_integrity_hash ON decision_lineage (integrity_hash)"))
            print("Added column 'integrity_hash' to 'decision_lineage'")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("Column 'integrity_hash' already exists.")
            else:
                print(f"Error adding 'integrity_hash': {e}")

        # Check for other tables/columns from Phase 31 if needed
        # ErrorFingerprint, LearningRecord, StrategyMemory are likely new tables, Base.metadata.create_all should handle them if they don't exist.
        
    print("Schema fix complete.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
