import asyncio
import os
from sqlalchemy import select
from libs.db.session import get_engine, AsyncSessionLocal
from libs.db.models.auth_models import Operator, PermissionGrant

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator))
        ops = res.scalars().all()
        for op in ops:
            print(f"Operator: {op.email} (Role: {op.role})")
            perms_res = await db.execute(select(PermissionGrant).where(PermissionGrant.operator_id == op.id))
            perms = perms_res.scalars().all()
            for p in perms:
                print(f"  - Permission: {p.permission} ({p.effect}) Scope: {p.scope_type}:{p.scope_value}")

if __name__ == "__main__":
    os.environ["PYTHONPATH"] = "."
    asyncio.run(check())
