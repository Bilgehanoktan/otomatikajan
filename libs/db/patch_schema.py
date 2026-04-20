
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from libs.db.session import AsyncSessionLocal
from sqlalchemy import text

async def patch():
    print("[*] Starting Schema Patch: decision_lineage.outcome...")
    async with AsyncSessionLocal() as db:
        try:
            # Check if column exists (optional but safer)
            await db.execute(text("ALTER TABLE decision_lineage ADD COLUMN outcome TEXT"))
            await db.commit()
            print("[+] SUCCESS: 'outcome' column added to decision_lineage.")
        except Exception as e:
            await db.rollback()
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print("[*] Column already exists, skipping.")
            else:
                print(f"[!] FAILED: {e}")
                sys.exit(1)

if __name__ == "__main__":
    asyncio.run(patch())
