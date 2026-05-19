
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine

# Add current directory to sys.path
sys.path.append(os.getcwd())

from libs.db.models.core_models import Base, SovereignEvidence

async def create_table():
    # Use the same fallback path as libs/db/session.py
    sqlite_url = "sqlite+aiosqlite:///./runtime/data/cortex_local.db"
    
    # Ensure directory exists
    os.makedirs("./runtime/data", exist_ok=True)
    
    print(f"Creating SovereignEvidence table on {sqlite_url}...")
    engine = create_async_engine(sqlite_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Table created successfully.")

if __name__ == "__main__":
    asyncio.run(create_table())
