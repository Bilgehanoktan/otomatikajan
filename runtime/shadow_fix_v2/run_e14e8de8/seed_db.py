import asyncio
import sys
import uuid
from datetime import datetime, timezone
sys.path.insert(0, '.')
from libs.db.session import async_session_factory
from libs.db.models.core_models import Project, ProjectStatus

async def async_main():
    async with async_session_factory() as db:
        p1 = Project(id=uuid.uuid4(), title='Workflow Alpha', status=ProjectStatus.RUNNING, created_at=datetime.now(timezone.utc))
        p2 = Project(id=uuid.uuid4(), title='Workflow Beta', status=ProjectStatus.WAITING_APPROVAL, created_at=datetime.now(timezone.utc))
        db.add(p1)
        db.add(p2)
        await db.commit()
        print('Seeded DB with Projects.')

if __name__ == '__main__':
    asyncio.run(async_main())
