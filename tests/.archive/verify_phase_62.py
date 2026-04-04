import asyncio
import uuid
from core.agi.operational.velocity_engine import VelocityEngine, EngineResult
from core.agi.world.provenance_engine import provenance_engine
from db.session import AsyncSessionLocal
from db.models import SovereignCodeFile, SovereignCodeResult
from sqlalchemy import select

async def verify_provenance_chain():
    print("--- Phase 62 Verification: Deep Provenance Indexing ---")
    
    # 1. Setup
    engine = VelocityEngine()
    project_id = uuid.uuid4()
    task_id = str(project_id)
    agent_id = "provenance_tester"
    
    # Mock Database entry for Project (required by FK)
    from db.models import Project, ProjectStatus
    async with AsyncSessionLocal() as db:
        new_proj = Project(
            id=project_id,
            title="Provenance Test Project",
            status="RUNNING"
        )
        db.add(new_proj)
        await db.commit()
    
    # Mock result with the 'FILE:' marker that our engine now scans for
    mock_result = EngineResult(
        success=True,
        output_data="I have updated the logic. FILE: core/test_file_62.py\nContent: print('Hello Provenance')",
        duration_s=0.5
    )
    
    # 2. Trigger Reflexive Logging (which calls ProvenanceEngine)
    print(f"\n[SCENARIO] Registering mutation for task {task_id}...")
    await engine._reflect_and_log(agent_id, mock_result, task_id)
    
    # 3. Verify Database Persistence
    print("Verifying database records...")
    async with AsyncSessionLocal() as db:
        # Check Result
        res_stmt = select(SovereignCodeResult).where(SovereignCodeResult.project_id == uuid.UUID(task_id))
        result_rec = (await db.execute(res_stmt)).scalar_one_or_none()
        
        assert result_rec is not None
        print(f"✅ SovereignCodeResult found: {result_rec.id}")
        
        # Check File & ProvenanceID
        file_stmt = select(SovereignCodeFile).where(SovereignCodeFile.result_id == result_rec.id)
        file_rec = (await db.execute(file_stmt)).scalar_one_or_none()
        
        assert file_rec is not None
        assert file_rec.path == "core/test_file_62.py"
        assert file_rec.provenance_id is not None
        print(f"✅ SovereignCodeFile found with ProvenanceID: {file_rec.provenance_id}")
        print(f"✅ File path correctly indexed: {file_rec.path}")

    print("\n✅ Phase 62 Verification SUCCESS: Deep Provenance chain is solid and persistent.")

if __name__ == "__main__":
    asyncio.run(verify_provenance_chain())
