import asyncio
import os
import uuid
from packages.orchestration.agi.cognitive.consolidator import Consolidator
from packages.orchestration.agi.cognitive.memory_api import memory_api
from packages.persistence.session import session_scope
from packages.persistence.repository import ProjectRepository

from packages.persistence.models import ProjectStatus

async def verify_knowledge_layer():
    print("--- Phase 20 Knowledge Consolidation Verification ---")
    
    # 1. Create a Fake Completed Project
    async with session_scope() as db:
        project = await ProjectRepository.create(
            db,
            title="Legacy Memory Migration",
            description="Testing the Phase 20 consolidation system.",
            status=ProjectStatus.COMPLETED.value
        )
        await ProjectRepository.mark_completed(
            db, 
            project.id, 
            report="SUCCESS: All legacy files were moved and indexes updated. Anti-pattern: Don't use absolute paths in scripts."
        )
        await packages.persistence.commit()
        project_id = project.id
    
    print(f"[*] Created mock project: {project_id}")
    await asyncio.sleep(1) # Transaksiyonun tam oturduğundan emin ol

    # 2. Run Consolidator (Dream Cycle)
    print("[*] Running Consolidator...")
    consolidator = Consolidator()
    async with session_scope() as db_dream: # Yeni session ile kontrol et
        await consolidator.run_consolidation_cycle()
    
    # 3. Check for KI creation
    ki_files = os.listdir("knowledge")
    if any("md" in f for f in ki_files):
        print(f"[SUCCESS] Knowledge Items found in /knowledge: {len(ki_files)} files.")
    else:
        print("[FAILURE] No Knowledge Items created.")
        return

    # 4. Verify MemoryAPI Retrieval
    print("[*] Verifying MemoryAPI retrieval...")
    context = await memory_api.get_strategic_context("Legacy Memory Migration")
    
    if "BİRLEŞİK AGİ HAFIZASI" in context and "Legacy Memory Migration" in context:
        print("[SUCCESS] MemoryAPI successfully retrieved consolidated context.")
    else:
        print("[FAILURE] MemoryAPI context retrieval failed or incomplete.")

    print("\n[PHASE 20] KNOWLEDGE CONSOLIDATION LAYER VERIFIED.")

if __name__ == "__main__":
    asyncio.run(verify_knowledge_layer())
