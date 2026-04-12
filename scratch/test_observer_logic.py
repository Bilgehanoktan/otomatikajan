
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import insert
from packages.persistence.session import get_db, init_db
from packages.persistence.models.core_models import SubTask, ProjectStatus, Project

async def simulate_failure():
    # 1. DB Hazırla
    await init_db()
    
    async with get_db() as db:
        # Önce bir dummy project oluştur (foreign key için)
        proj_id = uuid.uuid4()
        await db.execute(insert(Project).values(
            id=proj_id,
            title="Simulated Failure Project",
            description="Testing Improvement Observer",
            status=ProjectStatus.RUNNING
        ))
        
        # 2. Hatalı SubTask Ekle
        task_id = uuid.uuid4()
        await db.execute(insert(SubTask).values(
            id=task_id,
            project_id=proj_id,
            agent_id="test_agent_1",
            prompt="Write a broken script",
            result="ImportError: module not found",
            status=ProjectStatus.ERROR,
            attempts=3,
            completed_at=datetime.now(timezone.utc)
        ))
        await db.commit()
        print(f"OK: Simulated failure task created: {task_id}")

    # 3. Observer'ı Test Et
    from packages.improvement_engine.observer import ImprovementObserver
    observer = ImprovementObserver()
    print("SCAN: Scanning for opportunities...")
    ops = await observer.scan()
    
    found = False
    for op in ops:
        if str(task_id) == op.id:
            print(f"FIRE: SUCCESS: Observer caught the failure!")
            print(f"   Description: {op.description}")
            print(f"   Evidence: {op.evidence}")
            found = True
            break
    
    if not found:
        print("FAIL: Observer missed the simulated failure.")

if __name__ == "__main__":
    asyncio.run(simulate_failure())
