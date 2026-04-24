
import asyncio
import uuid
import bcrypt
from libs.db.session import get_db_ctx, init_db
from libs.db.models.core_models import User
from sqlalchemy import select

async def seed_admin():
    print("=== Initializing Database for Seeding ===")
    await init_db()
    
    async with get_db_ctx() as db:
        # Check if admin already exists
        email = "admin@sovereign.agi"
        res = await db.execute(select(User).where(User.email == email))
        user = res.scalar_one_or_none()
        
        if user:
            print(f"User {email} already exists. Skipping.")
            return
        
        print(f"Creating admin user: {email}")
        # Use bcrypt directly to match backend and avoid passlib issues
        password = "admin1234"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
        
        admin = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed,
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        await db.commit()
        print("Admin user created successfully.")

if __name__ == "__main__":
    asyncio.run(seed_admin())
