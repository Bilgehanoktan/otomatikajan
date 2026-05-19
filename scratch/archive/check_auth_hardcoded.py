import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from libs.db.models.auth_models import Base, Operator, PermissionGrant

# Hardcoded path from session.py logic
DB_PATH = os.path.abspath("runtime/data/cortex_local_v2.db").replace('\\', '/')
sqlite_url = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(sqlite_url)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator))
        ops = res.scalars().all()
        if not ops:
            print("No operators found in", DB_PATH)
        for op in ops:
            print(f"Operator: {op.email} (Role: {op.role})")

if __name__ == "__main__":
    os.environ["PYTHONPATH"] = "."
    asyncio.run(check())
