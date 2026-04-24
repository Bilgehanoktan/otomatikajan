import asyncio
import uuid
from bcrypt import hashpw, gensalt
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator

async def seed_admin():
    async with AsyncSessionLocal() as db:
        # 1. Admin kontrolü
        from sqlalchemy import select
        res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
        existing = res.scalar_one_or_none()
        
        if not existing:
            print("Admin operator not found, creating...")
            hashed = hashpw("admin123".encode(), gensalt(rounds=12)).decode()
            admin = Operator(
                id=uuid.uuid4(),
                email="admin@sovereign.agi",
                username="admin",
                hashed_password=hashed,
                role="SOVEREIGN_PRIME",
                is_active=True,
                department="governance",
                region="global"
            )
            db.add(admin)
            await db.commit()
            print("SUCCESS: Admin operator 'admin@sovereign.agi' created with password 'admin123'.")
        else:
            print("Admin operator already exists.")
            # Rolünü güncelle (garantiye al)
            existing.role = "SOVEREIGN_PRIME"
            await db.commit()
            print("SUCCESS: Admin role updated to SOVEREIGN_PRIME.")

if __name__ == "__main__":
    asyncio.run(seed_admin())
