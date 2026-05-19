
import asyncio
from sqlalchemy import text
from libs.db.session import get_engine

async def check_keys():
    engine = get_engine()
    async with engine.connect() as conn:
        res = await conn.execute(text('SELECT * FROM decision_lineage LIMIT 1'))
        print(f"Keys: {res.keys()}")

if __name__ == "__main__":
    asyncio.run(check_keys())
