import asyncio
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator
from sqlalchemy import select

async def get_user():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator).limit(1))
        u = res.scalar_one_or_none()
        if u:
            print(f'Active: {u.is_active}')
        else:
            print('None')

asyncio.run(get_user())
