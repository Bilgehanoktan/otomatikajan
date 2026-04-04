import asyncio
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import text
from db.session import AsyncSessionLocal, is_db_available

async def diagnose():
    print("--- [SEARCH] SOVEREIGN SYSTEM DIAGNOSTIC (Faz 12.1) ---")
    
    # 1. DB Availability
    db_ok = await is_db_available()
    print(f"Database Available: {'OK' if db_ok else 'ERROR'}")
    
    # 2. Latest Errors in ApiMetric
    try:
        from db.models import ApiMetric
        from sqlalchemy import select, desc
        async with AsyncSessionLocal() as db:
            stmt = select(ApiMetric).where(ApiMetric.status_code >= 400).order_by(ApiMetric.created_at.desc()).limit(5)
            res = await db.execute(stmt)
            errors = res.scalars().all()
            print(f"\nRecent API Errors ({len(errors)}):")
            for e in errors:
                print(f"  - [{e.created_at}] {e.method} {e.endpoint} -> {e.status_code} ({e.error_type})")
    except Exception as e:
        print(f"Error reading metrics: {e}")

    # 3. Cognitive Audit Integrity
    try:
        from db.models import ImprovementOpportunity
        async with AsyncSessionLocal() as db:
            count = await db.scalar(text("SELECT count(*) FROM improvement_opportunities"))
            print(f"\nImprovement Opportunities: {count}")
    except Exception as e:
        print(f"Error reading audits: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
