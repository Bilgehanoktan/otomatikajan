
import asyncio
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def check_tokens():
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.auth_models import RefreshToken
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(RefreshToken))
        tokens = res.scalars().all()
        print(f"TOTAL REFRESH TOKENS: {len(tokens)}")
        for t in tokens:
            print(f"ID: {t.id}, USER: {t.user_id}, REVOKED: {t.revoked}")

if __name__ == "__main__":
    asyncio.run(check_tokens())
