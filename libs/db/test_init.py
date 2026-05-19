
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import logging

from libs.db.session import get_engine


async def test():
    logging.basicConfig(level=logging.INFO)
    print("[*] Starting Force Postgres Init Test...")
    try:
        # We call the internal run_init by doing it manually or just init_db()
        # but we want to see the error.
        engine = get_engine()
        print(f"[*] Testing Engine: {engine.url}")

        from libs.db.session import run_init
        await run_init(engine)
        print("[+] INIT SUCCESSFUL!")

    except Exception as e:
        print(f"[!] INIT FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
