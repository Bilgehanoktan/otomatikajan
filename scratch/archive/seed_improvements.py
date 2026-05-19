
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from libs.db.session import get_db_ctx, init_db
from libs.db.models.core_models import SystemImprovement
from sqlalchemy import select

async def seed_improvements():
    print("=== Seeding System Improvements (Patches) ===")
    await init_db()
    
    async with get_db_ctx() as db:
        # 1. Verified Patch
        i1 = SystemImprovement(
            id=uuid.uuid4(),
            target_file="libs/infra/middleware.py",
            instruction="Optimize CORS pre-flight response caching.",
            proposed_patch="- max_age=600\n+ max_age=3600",
            status="verified",
            risk_score=0.12,
            created_at=datetime.now(timezone.utc) - timedelta(hours=5)
        )
        db.add(i1)
        
        # 2. Pending Patch
        i2 = SystemImprovement(
            id=uuid.uuid4(),
            target_file="services/workflow_api/main.py",
            instruction="Increase Uvicorn worker timeout for heavy batch loads.",
            proposed_patch="- timeout=30\n+ timeout=60",
            status="pending",
            risk_score=0.45,
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        db.add(i2)

        await db.commit()
        print("Improvements seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_improvements())
