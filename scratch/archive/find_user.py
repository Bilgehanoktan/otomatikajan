
import asyncio
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def find_user():
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.auth_models import Operator
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator).limit(1))
        user = res.scalar_one_or_none()
        if user:
            print(f"USER_ID: {user.id}")
            print(f"EMAIL: {user.email}")
            print(f"ROLE: {user.role}")
        else:
            print("NO OPERATOR FOUND")

if __name__ == "__main__":
    asyncio.run(find_user())
