
import asyncio
from libs.db.session import init_db, session_scope
from libs.db.models.lineage_models import DecisionLineage
from sqlalchemy import select

async def check():
    await init_db()
    async with session_scope() as s:
        res = await s.execute(select(DecisionLineage).where(DecisionLineage.decision_type == 'SYSTEM_EVOLUTION'))
        items = res.scalars().all()
        print(f'SYSTEM_EVOLUTION items: {len(items)}')
        for i in items:
            print(f'- {i.id}: {i.rationale}')

if __name__ == "__main__":
    asyncio.run(check())
