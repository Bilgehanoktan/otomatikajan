import asyncio
import sys
sys.path.insert(0, '.')
from libs.db.session import get_engine, init_db

async def main():
    await init_db()
    engine = get_engine()
    print(f"Engine URL: {engine.url}")

if __name__ == "__main__":
    asyncio.run(main())
