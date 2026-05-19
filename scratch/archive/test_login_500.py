
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Mocking parts of the system
from libs.config import DATABASE_URL
from libs.db.models.auth_models import Operator, RefreshToken
from services.auth.jwt_auth import _make_token, JWT_SECRET, ACCESS_MINUTES, REFRESH_DAYS

async def test_login_logic():
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get first operator
            result = await db.execute(select(Operator).limit(1))
            operator = result.scalar_one_or_none()
            if not operator:
                print("No operator found")
                return

            print(f"Testing login for: {operator.email}")
            
            # 1. Access Token
            access = _make_token({
                "sub": str(operator.id),
                "email": operator.email,
                "type": "access",
                "identity_type": "operator",
                "role": operator.role
            }, timedelta(minutes=ACCESS_MINUTES))
            print(f"Access token generated (Length: {len(access)})")

            # 2. Refresh Token
            refresh = _make_token({"sub": str(operator.id), "type": "refresh"}, timedelta(days=REFRESH_DAYS))
            print(f"Refresh token generated (Length: {len(refresh)})")

            # 3. DB Save
            rt = RefreshToken(
                id=uuid.uuid4(),
                user_id=operator.id, 
                token=refresh, 
                expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS)
            )
            db.add(rt)
            await db.commit()
            print("Refresh token saved successfully")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_login_logic())
