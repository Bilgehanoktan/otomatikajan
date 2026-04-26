
import uuid
import sys
import os
import sqlite3
import asyncio
from bcrypt import hashpw, gensalt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Path discovery
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from libs.db.models.auth_models import Operator
from libs.db.session import get_engine_url, is_db_degraded

async def create_admin(email, password, username=None):
    url = get_engine_url()
    is_sqlite = is_db_degraded()
    
    # SQLite direct fix if needed, but let's try SQLAlchemy first
    engine = create_async_engine(url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if exists
        res = await session.execute(select(Operator).where(Operator.email == email))
        existing = res.scalar_one_or_none()
        
        hashed = hashpw(password.encode(), gensalt(rounds=12)).decode()
        
        if existing:
            print(f"Updating existing user {email} to SOVEREIGN_PRIME role...")
            existing.role = "SOVEREIGN_PRIME"
            existing.hashed_password = hashed
            existing.is_active = True
        else:
            print(f"Creating new SOVEREIGN_PRIME: {email}")
            op = Operator(
                email=email,
                username=username or email.split('@')[0],
                hashed_password=hashed,
                role="SOVEREIGN_PRIME",
                is_active=True
            )
            session.add(op)
            
        await session.commit()
        print("Success! Admin account is ready.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python manage_admin.py <email> <password> [username]")
        sys.exit(1)
        
    email = sys.argv[1]
    pwd = sys.argv[2]
    uname = sys.argv[3] if len(sys.argv) > 3 else None
    
    asyncio.run(create_admin(email, pwd, uname))
