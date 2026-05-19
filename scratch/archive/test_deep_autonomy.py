
import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone

# Workspace root ekle
sys.path.append("e:/ai_company_faz12.1")

from services.orchestration.agi.cognitive.axiology_engine import axiology_engine
from services.improve.repair_memory import RepairMemory, RepairMemoryEntry
from services.repair.improvement.observer import observer
from services.repair.improvement.gate import improvement_gate
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import WorkflowEvent, SubTask, ImprovementOpportunity
from sqlalchemy import delete

# ASCII GÃ¼venli print fonksiyonu
def safe_print(msg):
    try:
        print(msg.encode('ascii', 'ignore').decode('ascii'))
    except:
        print("[Print Error] Context hidden due to encoding.")

async def test_axiology_memory():
    safe_print("\n--- TEST 1: Axiology Experience Integration ---")
    memory = RepairMemory()
    await memory.ensure_initialized()
    
    # 1. Sahte bir baÅŸarÄ±sÄ±zlÄ±k tecrÃ¼besi ekle
    fail_entry = RepairMemoryEntry(
        id=str(uuid.uuid4()),
        case_id="incident_x",
        incident_type="bug",
        subsystem="core",
        patch_strategy="radical",
        outcome="failure",
        failure_reason="System crash",
        score=0.1,
        timestamp=datetime.now()
    )
    memory.record_outcome(fail_entry)
    safe_print("[OK] Recorded radical strategy FAILURE in memory.")

    # 2. Axiology'den bu stratejiyi iÃ§eren bir yamayÄ± deÄŸerlendirmesini iste
    target_patch = "Apply RADICAL refactor to core/orchestrator.py to fix everything."
    result = await axiology_engine.evaluate_alignment(target_patch, context="system_repair_patch")
    
    safe_print(f"Decision: {result.get('decision')}")
    justification = result.get('justification', '')
    safe_print(f"Justification: {justification}")
    
    # EÄŸer tecrÃ¼be negatifse "flag" bekliyoruz
    if result.get("decision") in ["flag", "reject"]:
        safe_print("[SUCCESS] Axiology remembered the failure and penalized the strategy!")
    else:
        safe_print("[FAILURE] Axiology ignored the historical failure.")

async def test_improvement_loop():
    safe_print("\n--- TEST 4: Self-Correction Loop (Affected Files) ---")
    
    async with AsyncSessionLocal() as session:
        # Temizlik
        await session.execute(delete(ImprovementOpportunity))
        await session.execute(delete(WorkflowEvent))
        await session.execute(delete(SubTask))
        await session.commit()

        # 1. Sahte bir hata senaryosu yarat (WorkflowEvent + SubTask)
        # 2 adet hata yaratmalÄ±yÄ±z Ã§Ã¼nkÃ¼ observer "having(count >= 2)" bekliyor
        target_file = "services/auth/core.py"
        
        from libs.db.models.core_models import ProjectStatus
        for i in range(2):
            test_id = uuid.uuid4()
            subtask = SubTask(
                id=test_id,
                agent_id="test-agent",
                action="edit",
                prompt="Fix auth",
                input_data={"target_file": target_file},
                status=ProjectStatus.FAILED,
                created_at=datetime.now(timezone.utc)
            )
            
            event = WorkflowEvent(
                id=uuid.uuid4(),
                step_id=str(test_id),
                event_type="step_failed",
                payload={"error": "SyntaxError: invalid syntax", "agent_id": "test-agent"},
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(subtask)
            session.add(event)
        
        await session.commit()
        safe_print(f"[OK] Created 2 dummy failures for {target_file}")

    # 2. Observer'Ä± Ã§alÄ±ÅŸtÄ±r
    safe_print("Scanning for issues...")
    opps = await observer.scan()
    
    found = False
    for opp in opps:
        if target_file in opp.affected_files:
            safe_print(f"[SUCCESS] Observer found the issue and identified affected file: {opp.affected_files}")
            found = True
            break
    
    if not found:
        safe_print(f"[FAILURE] Observer missed the affected file. (Found {len(opps)} opportunities)")
        for o in opps: safe_print(f" - {o.title}: {o.affected_files}")
        return

    # 3. Gate'i Ã§alÄ±ÅŸtÄ±r (Persistence Test)
    safe_print("Running improvement gate cycle...")
    await improvement_gate.run_cycle()
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        res = await session.execute(select(ImprovementOpportunity))
        saved = res.scalars().all()
        if len(saved) > 0:
            safe_print(f"[SUCCESS] ImprovementOpportunity persisted to DB. (Total: {len(saved)})")
        else:
            safe_print("[FAILURE] ImprovementOpportunity not saved to DB.")

async def main():
    await test_axiology_memory()
    await test_improvement_loop()

if __name__ == "__main__":
    asyncio.run(main())
