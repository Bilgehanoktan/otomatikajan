
import asyncio
import os
import sys
from datetime import datetime, timezone

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, project_root)

from services.improve.repair_bench import RepairBenchService
from libs.llm.model_orchestrator import ModelOrchestrator
from libs.db.session import init_db, session_scope, is_db_degraded
from libs.db.models.repair_models import RepairBenchmarkRun, RepairTournament
from sqlalchemy import select

async def validate_repair_lab():
    print("Starting Repair Lab Validation...")
    
    # 1. Initialize DB (SQLite fallback will trigger if Docker is down)
    await init_db()
    
    if is_db_degraded():
        print("Warning: Primary DB unreachable. Operating in SQLite Fallback mode.")
    else:
        print("OK: Primary DB (Postgres) is reachable.")

    # 2. Setup Service
    model_orch = ModelOrchestrator()
    service = RepairBenchService(model_orch=model_orch)
    
    # 3. List all cases
    cases = service.loader.list_all_cases()
    print(f"Total Benchmark Cases: {len(cases)}")
    
    if not cases:
        print("No cases found in benchmarks/repair_bench/cases")
        return

    # 4. Run a single case (Simulated or Real)
    # We'll try to run the first case.
    target_case = cases[0]
    print(f"Running benchmark for case: {target_case.id} ({target_case.title})")
    
    try:
        # Note: This might fail if LLM keys are missing, but we want to check the DB flow
        result = await service.run_benchmark_case(target_case.id)
        if result:
            print(f"Benchmark completed: Success={result.success}, Score={result.score}")
        else:
            print("Benchmark returned None.")
    except Exception as e:
        print(f"Benchmark failed with error: {e}")

    # 5. Verify DB Persistence
    async with session_scope() as session:
        # Check tournaments
        res = await session.execute(select(RepairTournament).order_by(RepairTournament.created_at.desc()))
        tourneys = res.scalars().all()
        print(f"Tournaments in DB: {len(tourneys)}")
        for t in tourneys[:3]:
            print(f"  - Tournament: {t.tournament_id}, Score: {t.winner_score}")

        # Check Decision Lineage (Improvements use this)
        from libs.db.models.lineage_models import DecisionLineage
        res_lin = await session.execute(select(DecisionLineage).order_by(DecisionLineage.created_at.desc()).limit(5))
        lineages = res_lin.scalars().all()
        print(f"Decision Lineages in DB: {len(lineages)}")
        for l in lineages:
            print(f"  - Lineage: {l.id}, Type: {l.decision_type}, Comp: {l.component_name}")

    # 6. Verify Lab Stats
    stats = await service.get_lab_stats()
    print(f"Lab Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(validate_repair_lab())
