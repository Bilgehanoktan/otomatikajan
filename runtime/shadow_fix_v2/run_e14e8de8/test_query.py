import asyncio
from sqlalchemy import select, func, desc
from libs.db.session import AsyncSessionLocal, init_db
from libs.db.models.core_models import Project, SystemImprovement
from libs.db.models.learning_models import ErrorFingerprint

async def test_dashboard():
    print("Testing dashboard queries...")
    async with AsyncSessionLocal() as db:
        print("Executing Workflow Stats...")
        res_wf = await db.execute(
            select(Project.status, func.count(Project.id).label("cnt")).group_by(Project.status)
        )
        wf_rows = res_wf.all()
        print("Workflow Stats:", wf_rows)

        print("Executing ErrorFingerprint count...")
        f_count = (
            await db.execute(
                select(func.count(ErrorFingerprint.id)).where(
                    ErrorFingerprint.is_active == True,
                    ErrorFingerprint.severity.in_(["warning", "medium", "high", "critical"])
                )
            )
        ).scalar() or 0
        print("f_count:", f_count)

asyncio.run(test_dashboard())
