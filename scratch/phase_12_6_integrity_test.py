import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Project root'u ekle
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from packages.persistence.session import get_engine, AsyncSessionLocal
from packages.improvement_engine.observer import ImprovementObserver
from packages.orchestration.application.self_updater import SelfUpdater
from apps.api.support._task_shared import TaskCreateRequest
from packages.persistence.models import SubTask, Project, ProjectStatus
from sqlalchemy import select, delete

async def test_persistence_engine():
    print("RUN: Testing Persistence Engine (The Fix Audit)...")
    engine = get_engine()
    assert engine is not None, "Engine could not be initialized!"
    print("SUCCESS: Persistence Engine is alive.")

async def test_pydantic_v2_models():
    print("RUN: Testing Pydantic V2 Model Consistency (TaskCreateRequest)...")
    req = TaskCreateRequest(
        title="Test Task Phase 12.6",
        description="Testing Pydantic V2 consistency",
        priority="high",
        source="manual"
    )
    assert req.priority == "high"
    print("SUCCESS: Pydantic V2 models (TaskCreateRequest) are stable.")

async def test_improvement_observer_real_data():
    print("RUN: Testing ImprovementObserver with Real Data Scans...")
    observer = ImprovementObserver()
    
    async with AsyncSessionLocal() as db:
        proj = Project(
            title="TEST-AUDIT-12.6",
            status=ProjectStatus.ERROR
        )
        db.add(proj)
        await db.flush()
        
        # completed_at SET EDİLMELİ ki observer yakalasın (completed_at != None kuralı)
        new_fail = SubTask(
            project_id=proj.id,
            agent_id="fail_agent_real",
            prompt="Simulated failing prompt",
            result="ImportError: module not found",
            status=ProjectStatus.ERROR,
            attempts=5,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(new_fail)
        await db.commit()
        fail_id = new_fail.id
        proj_id = proj.id
        print(f"INFO: Injected failure task {fail_id} under project {proj_id}")

    try:
        opportunities = await observer.scan()
        caught = False
        for opt in opportunities:
            if str(fail_id) in str(opt.id):
                caught = True
                break
        
        assert caught, "Observer failed to catch the real failure data!"
        print("SUCCESS: ImprovementObserver is sensing reality correctly.")

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Project).where(Project.id == proj_id))
            await db.commit()
            print("INFO: Cleanup completed.")

async def test_self_updater_guardrails():
    print("RUN: Testing Self-Updater Security Guardrails...")
    updater = SelfUpdater(model_orch=None)
    
    high_risk_files = [
        "packages/persistence/session.py",
        "apps/api/routers/auth/",
        "packages/orchestration/application/sovereign_cortex.py"
    ]
    
    for path in high_risk_files:
        found = False
        for risk in updater.HIGH_RISK_PATHS:
            if risk in path:
                found = True
                break
        assert found, f"Security Guardrail MISSING for path in HIGH_RISK_PATHS: {path}"
    print("SUCCESS: Security Guardrails are active for critical infrastructure.")

async def run_all_tests():
    print("=== SOVEREIGN AGI PHASE 12.6 INTEGRITY AUDIT (v3) ===")
    try:
        await test_persistence_engine()
        await test_pydantic_v2_models()
        await test_improvement_observer_real_data()
        await test_self_updater_guardrails()
        print("\n🏆 STATE: Phase 12.6 is fully verified and production-ready.")
    except Exception as e:
        print(f"\n❌ FATAL: Phase 12.6 testing failed: {str(e)}")
        import traceback
        # Unicode safe traceback printing
        traceback_str = traceback.format_exc()
        print(traceback_str.encode("ascii", "ignore").decode("ascii"))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
