import asyncio
import uuid
from bcrypt import hashpw, gensalt
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator
from sqlalchemy import select

async def reset_admin_password():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
        admin = res.scalar_one_or_none()
        
        hashed = hashpw("admin123".encode(), gensalt(rounds=12)).decode()
        
        if not admin:
            print("Admin not found, creating new...")
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
        else:
            print("Admin found, force resetting password...")
            admin.hashed_password = hashed
            admin.role = "SOVEREIGN_PRIME"
            admin.is_active = True
            
        await db.commit()
        print("SUCCESS: Admin 'admin@sovereign.agi' password reset to 'admin123'.")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
