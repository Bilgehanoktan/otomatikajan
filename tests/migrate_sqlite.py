import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def migrate_sqlite():
    print(f"SRE HARDENING: SQLite Migrations for Phase 51...")
    print(f"Target: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # 1. subtasks tablosu (Faz 51 DAG)
        subtask_cols = [
            ("parent_id", "CHAR(36)"), 
            ("dependencies", "JSON"),  
            ("is_complex", "BOOLEAN DEFAULT FALSE"), 
            ("prompt", "TEXT")
        ]
        for col, col_type in subtask_cols:
            try:
                await conn.execute(text(f"ALTER TABLE subtasks ADD COLUMN {col} {col_type}"))
            except Exception: pass
            
        # 2. memories tablosu (Faz 51 Hierarchical Memory)
        memory_cols = [
            ("parent_id", "CHAR(36)"),
            ("cause_id", "CHAR(36)"),
            ("project_id", "CHAR(36)") # Bazı şemalar için eksik olabilir
        ]
        for col, col_type in memory_cols:
            try:
                await conn.execute(text(f"ALTER TABLE memories ADD COLUMN {col} {col_type}"))
                print(f"[+] memories kolonu eklendi: {col}")
            except Exception: pass

    await engine.dispose()
    print("SRE HARDENING: SQLite Migration completed.")

if __name__ == "__main__":
    asyncio.run(migrate_sqlite())
