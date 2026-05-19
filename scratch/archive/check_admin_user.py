
import asyncio
import os
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator
from sqlalchemy import select

async def check_users():
    print("Checking Database for Admin User...")
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator))
        users = res.scalars().all()
        print(f"Users found: {[u.email for u in users]}")
        
        admin = next((u for u in users if u.email == "admin@sovereign.agi"), None)
        if not admin:
            print("CRITICAL: admin@sovereign.agi NOT FOUND. Creating it now...")
            from bcrypt import hashpw, gensalt
            hashed = hashpw("admin1234".encode(), gensalt()).decode()
            new_admin = Operator(
                email="admin@sovereign.agi",
                username="admin",
                hashed_password=hashed,
                role="SOVEREIGN_PRIME",
                is_active=True
            )
            db.add(new_admin)
            await db.commit()
            print("Admin user created successfully.")
        else:
            print(f"Admin user exists. Role: {admin.role}")

if __name__ == "__main__":
    asyncio.run(check_users())
