
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from db.models import Base
# Import all models to ensure they are registered with Base
import db.models
import db.repair_models

async def force_init():
    database_url = "sqlite+aiosqlite:///./cortex_local.db"
    print(f"Force initializing database: {database_url}")
    
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        print("Running Base.metadata.create_all...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")
        
        # Verify api_metrics specifically
        res = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='api_metrics'"))
        table_exists = res.fetchone()
        if table_exists:
            print("CONFIRMED: 'api_metrics' table exists.")
        else:
            print("FAILED: 'api_metrics' table still missing!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(force_init())
