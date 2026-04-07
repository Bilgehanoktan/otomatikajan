import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def try_fix(port: int):
    url = f"postgresql+asyncpg://postgres:postgres@127.0.0.1:{port}/ai_company"
    print(f"Trying port {port}...")
    engine = create_async_engine(url, connect_args={"timeout": 5})
    try:
        async with engine.begin() as conn:
            print(f"Connected to {port}!")
            await conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_limit FLOAT DEFAULT 0.0"))
            print(f"Successfully ensured budget_limit column on port {port}!")
            return True
    except Exception as e:
        print(f"Port {port} failed: {e}")
        return False
    finally:
        await engine.dispose()

async def main():
    if not await try_fix(5432):
        if not await try_fix(5433):
            print("Both ports failed. Please ensure Postgres is running.")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
