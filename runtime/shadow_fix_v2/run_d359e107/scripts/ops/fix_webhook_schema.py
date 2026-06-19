import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from sqlalchemy import text

async def fix():
    async with AsyncSessionLocal() as db:
        # PostgreSQL syntax for adding column if not exists
        try:
            await db.execute(text('ALTER TABLE webhook_subscriptions ADD COLUMN owner_id UUID REFERENCES users(id) ON DELETE CASCADE;'))
            await db.commit()
            print('Column owner_id added to webhook_subscriptions')
        except Exception as e:
            print(f'Error (might already exist): {e}')

if __name__ == "__main__":
    asyncio.run(fix())
