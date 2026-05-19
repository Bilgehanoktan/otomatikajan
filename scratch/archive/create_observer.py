import asyncio
import os
import uuid
from sqlalchemy import select
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator
from services.auth.jwt_auth import auth_service

async def create_observer():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator).where(Operator.email == "bilgehan@faz.one"))
        op = res.scalar_one_or_none()
        
        if op:
            print(f"Updating operator {op.email}")
            # we need to hash the password if we update manually, 
            # but let's use the register logic or just update the role if it exists.
            op.role = "AUDIT_OBSERVER"
            op.is_active = True
            # For simplicity, if it exists, we assume we know the password or we can use AuthService to reset it.
            # But let's just use the register logic if it doesn't exist.
        else:
            print("Creating operator bilgehan@faz.one via register")
            await auth_service.register(db, "bilgehan@faz.one", "bilgehan123", "bilgehan")
            
            # Now fetch and update role
            res = await db.execute(select(Operator).where(Operator.email == "bilgehan@faz.one"))
            op = res.scalar_one_or_none()
            op.role = "AUDIT_OBSERVER"
        
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    os.environ["PYTHONPATH"] = "."
    asyncio.run(create_observer())
