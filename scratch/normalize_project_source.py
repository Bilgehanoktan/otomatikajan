import asyncio
from sqlalchemy import text
from libs.db.session import AsyncSessionLocal

async def main():
    source_mapping = {
        'api': 'API',
        'manual': 'MANUAL',
        'telegram': 'TELEGRAM',
        'scheduled': 'SCHEDULED',
        'queue_stuck': 'QUEUE_STUCK',
        'approval_timeout': 'APPROVAL_TIMEOUT',
        'control_plane': 'CONTROL_PLANE',
        'ceo': 'CEO',
        'CEO': 'CEO',
    }
    async with AsyncSessionLocal() as db:
        total = 0
        for src, dst in source_mapping.items():
            res = await db.execute(text('UPDATE projects SET source = :dst WHERE source = :src'), {'src': src, 'dst': dst})
            total += res.rowcount or 0
        await db.commit()
        print('UPDATED_PROJECT_SOURCE_ROWS=', total)

asyncio.run(main())
