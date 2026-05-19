
import asyncio
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def check_admin():
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.auth_models import Operator
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
        user = res.scalar_one_or_none()
        if user:
            print(f"ID: {user.id}")
            print(f"EMAIL: {user.email}")
            print(f"HASH: {user.hashed_password}")
            print(f"ACTIVE: {user.is_active}")
            print(f"ROLE: {user.role}")
        else:
            print("ADMIN NOT FOUND")

if __name__ == "__main__":
    asyncio.run(check_admin())
