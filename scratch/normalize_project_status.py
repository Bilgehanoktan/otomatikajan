import asyncio
from sqlalchemy import text
from libs.db.session import AsyncSessionLocal

async def main():
    mapping = {
        'pending': 'PENDING',
        'queued': 'QUEUED',
        'running': 'RUNNING',
        'waiting': 'WAITING',
        'pending_approval': 'PENDING_APPROVAL',
        'waiting_approval': 'WAITING_APPROVAL',
        'completed': 'COMPLETED',
        'failed': 'FAILED',
        'error': 'ERROR',
        'cancelled': 'CANCELLED',
        'canceled': 'CANCELLED',
        'paused': 'PAUSED',
    }
    async with AsyncSessionLocal() as db:
        total = 0
        for src, dst in mapping.items():
            res = await db.execute(text('UPDATE projects SET status = :dst WHERE status = :src'), {'src': src, 'dst': dst})
            total += res.rowcount or 0
        await db.commit()
        print('UPDATED_PROJECT_STATUS_ROWS=', total)

asyncio.run(main())
