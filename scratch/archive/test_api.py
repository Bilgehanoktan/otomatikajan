
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

async def test_fingerprints():
    try:
        from libs.db.session import AsyncSessionLocal
        from libs.db.models.learning_models import ErrorFingerprint
        from sqlalchemy import select, func
        from services.workflow_api.governance_router import FingerprintOut

        async with AsyncSessionLocal() as db:
            print("[Test] Checking database connection...")
            count_q = select(func.count(ErrorFingerprint.id))
            total_count = (await db.execute(count_q)).scalar()
            print(f"[Test] Total fingerprints in DB: {total_count}")

            q = select(ErrorFingerprint).limit(5)
            res = await db.execute(q)
            items = res.scalars().all()
            
            print(f"[Test] Mapping {len(items)} items to FingerprintOut...")
            for i in items:
                out = FingerprintOut(
                    id=str(i.id),
                    error_family=i.error_family,
                    service=i.service,
                    component=i.component,
                    severity=i.severity,
                    recurrence_count=i.recurrence_count,
                    first_seen_at=i.first_seen_at,
                    last_seen_at=i.last_seen_at,
                    normalized_message=i.normalized_message,
                    risk_domain=i.risk_domain,
                    is_active=i.is_active,
                    meta_data=i.meta_data
                )
                print(f"[Test] Success mapping ID: {out.id}")
            
            print("[Test] ALL GOOD")
    except Exception as e:
        print(f"[Test] ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fingerprints())
