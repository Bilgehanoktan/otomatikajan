import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from packages.persistence.session import _get_engine
from sqlalchemy import inspect

async def inspect_projects():
    print("🚀 Veritabanı Teftişi (SQLAlchemy Inspect)...")
    engine = _get_engine()
    
    def get_cols(conn):
        inst = inspect(conn)
        return inst.get_columns("projects")

    async with engine.connect() as conn:
        cols = await conn.run_sync(get_cols)
        print(f"📦 'projects' tablosunda {len(cols)} kolon bulundu:")
        for col in cols:
            print(f"- {col['name']} ({col['type']}), Nullable: {col['nullable']}")

if __name__ == "__main__":
    asyncio.run(inspect_projects())
