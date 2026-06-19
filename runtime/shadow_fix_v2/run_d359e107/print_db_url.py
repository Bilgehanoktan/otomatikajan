import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db.session import AsyncSessionLocal, get_engine, DATABASE_URL
from services.orchestration.ceo.engine import get_ceo_engine

async def check():
    print(f"DATABASE_URL variable: {DATABASE_URL}")
    engine = get_engine()
    print(f"SQLAlchemy Engine URL: {engine.url}")

if __name__ == "__main__":
    asyncio.run(check())
