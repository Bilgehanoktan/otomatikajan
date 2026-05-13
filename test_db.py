import asyncio
from libs.db.session import AsyncSessionLocal
from sqlalchemy import text

async def test():
    print("Testing DB connection...")
    async with AsyncSessionLocal() as db:
        print("Got session...")
        res = await db.execute(text('SELECT 1'))
        print("Result:", res.scalar())

asyncio.run(test())
