
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from libs.db.session import AsyncSessionLocal, get_engine
from sqlalchemy import text

async def inspect():
    engine = get_engine()
    print(f"[*] Engine URL: {engine.url}")
    async with AsyncSessionLocal() as db:
        try:
            # Get column names
            res = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'decision_lineage'"))
            columns = [r[0] for r in res.all()]
            print(f"[*] Columns in 'decision_lineage': {columns}")
            
            if 'outcome' not in columns:
                print("[!] 'outcome' is MISSING!")
            else:
                print("[+] 'outcome' is PRESENT.")
                
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
