
import asyncio
from libs.db.session import init_db, session_scope
from libs.db.models import Operator
from sqlalchemy import select

async def check():
    await init_db()
    async with session_scope() as s:
        res = await s.execute(select(Operator))
        items = res.scalars().all()
        print(f'Operators: {len(items)}')
        for i in items:
            print(f'- {i.email}: {i.role}')

if __name__ == "__main__":
    asyncio.run(check())
