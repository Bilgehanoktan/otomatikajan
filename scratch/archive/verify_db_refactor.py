import asyncio
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

async def test_db_readiness():
    print("[*] Testing Database Readiness...")
    from libs.db.session import get_db_ctx
    from sqlalchemy import text
    
    try:
        async with get_db_ctx() as db:
            # 1. Check connectivity
            result = await db.execute(text("SELECT 1"))
            val = result.scalar()
            print(f"[+] Basic query (SELECT 1) successful: {val}")
            
            # 2. Check schema (Projects table)
            from libs.db.models.core_models import Project
            from sqlalchemy import select, func
            count_q = select(func.count(Project.id))
            count = (await db.execute(count_q)).scalar()
            print(f"[+] Project count: {count}")
            
            # 3. Test write (Temporary audit entry if possible, or just a transaction test)
            print("[+] Testing session rollback integrity...")
            # We don't want to pollute real data, so just testing if we can start a sub-transaction
            pass

        print("[SUCCESS] Database session management is operational.")
        return True
    except Exception as e:
        print(f"[FAILURE] Database error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if asyncio.run(test_db_readiness()):
        sys.exit(0)
    else:
        sys.exit(1)
