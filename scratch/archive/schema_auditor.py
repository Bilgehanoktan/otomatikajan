import os
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from libs.config import DATABASE_URL
from libs.db.base import Base

# Import all models to ensure they are registered with Base.metadata
from libs.db.models import lineage_models, learning_models

async def audit_schema():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print(f"Auditing database: {DATABASE_URL}")
        
        # Get list of tables (DB agnostic-ish)
        if "sqlite" in DATABASE_URL:
            res = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        else:
            res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        
        db_tables = [r[0] for r in res.fetchall()]
        print(f"Tables in DB: {db_tables}")
        
        for table_name, table in Base.metadata.tables.items():
            if table_name not in db_tables:
                print(f"[MISSING TABLE] {table_name}")
                continue
                
            print(f"Checking table: {table_name}")
            # Get columns in DB
            if "sqlite" in DATABASE_URL:
                res = await conn.execute(text(f"PRAGMA table_info({table_name})"))
                db_cols = [r[1] for r in res.fetchall()] # Column name is the second field in PRAGMA table_info
            else:
                res = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"))
                db_cols = [r[0] for r in res.fetchall()]
            
            model_cols = table.columns.keys()
            
            missing_in_db = [c for c in model_cols if c not in db_cols]
            extra_in_db = [c for c in db_cols if c not in model_cols]
            
            if missing_in_db:
                print(f"  [MISSING COLUMNS] {missing_in_db}")
            if extra_in_db:
                print(f"  [EXTRA COLUMNS] {extra_in_db}")
            if not missing_in_db:
                print(f"  [OK] All model columns present.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(audit_schema())
