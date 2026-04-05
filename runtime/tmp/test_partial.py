
import os
import sys

# Set environment
os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///tmp_test_db.db"

import asyncio
# Add project root to sys.path
sys.path.insert(0, os.getcwd())

from db.session import get_db, _get_engine
from db.repository import ProjectRepository
from db.models import ProjectStatus, ProjectSource, Base

async def test():
    print("Testing PARTIAL_COMPLETE state machine on SQLite...", flush=True)
    engine = _get_engine()
    
    # MANUALLY initialize schema
    async with engine.begin() as conn:
        print("Creating tables...", flush=True)
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created.", flush=True)

    async with get_db() as db:
        # 1. Create a dummy project
        project = await ProjectRepository.create(
            db,
            title="Test Partial State",
            description="Testing state transitions",
            priority="medium",
            source=ProjectSource.MANUAL.value
        )
        pid = project.id
        print(f"Created project: {pid}", flush=True)
        
        # 2. Update to PARTIAL_COMPLETE
        print("Updating status to PARTIAL_COMPLETE via mark_completed...", flush=True)
        await ProjectRepository.mark_completed(
            db, 
            pid, 
            report="Kısmi başarı raporu.", 
            status=ProjectStatus.PARTIAL_COMPLETE
        )
        
        # 3. Fetch and verify
        p = await ProjectRepository.get(db, pid)
        print(f"Project Status: {p.status}", flush=True)
        print(f"Progress Pct: {p.progress_pct}%", flush=True)
        
        # FAZ 12 requirement: Terminal state must have 100% progress
        assert p.status == ProjectStatus.PARTIAL_COMPLETE
        assert p.progress_pct == 100
        
        print("Test passed successfully!", flush=True)

    # Cleanup
    await engine.dispose()
    await asyncio.sleep(0.5)
    if os.path.exists("tmp_test_db.db"):
        os.remove("tmp_test_db.db")
        print("Cleaned up SQLite file.", flush=True)

if __name__ == "__main__":
    asyncio.run(test())
