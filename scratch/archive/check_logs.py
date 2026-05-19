
import asyncio
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def check_logs():
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import DomainEventLog
    from sqlalchemy import select, desc
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(DomainEventLog)
            .where(DomainEventLog.event_type.like("log.error%"))
            .order_by(desc(DomainEventLog.created_at))
            .limit(10)
        )
        logs = res.scalars().all()
        
        print(f"--- SON 10 HATA LOGU ({len(logs)}) ---")
        for l in logs:
            print(f"ZAMAN: {l.created_at}")
            print(f"TİP: {l.event_type}")
            print(f"MESAJ: {l.message}")
            print(f"PAYLOAD: {l.payload}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_logs())
