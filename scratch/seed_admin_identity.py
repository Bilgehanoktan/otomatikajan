import asyncio
from sqlalchemy import select
from libs.db.session import async_session
from libs.db.models import User
import bcrypt

async def main():
    async with async_session() as db:
        hashed = bcrypt.hashpw(b"admin1234", bcrypt.gensalt(12)).decode()
        result = await db.execute(select(User).where(User.email=="admin@sovereign.agi"))
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = hashed
            user.is_admin = True
            user.is_active = True
            await db.commit()
            print("Password updated for admin@sovereign.agi")
        else:
            print("User not found")

if __name__ == "__main__":
    asyncio.run(main())
