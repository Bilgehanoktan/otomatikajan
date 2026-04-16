
import asyncio
from services.improve.benchmark_loader import RepairBenchLoader
from services.improve.repair_bench import RepairBenchService

async def main():
    print("--- [PHASE 28] Testing Repair Lab Loader ---")
    loader = RepairBenchLoader()
    cases = loader.list_all_cases()
    print(f"Loaded {len(cases)} cases.")
    
    for case in cases:
        print(f"\n[CASE] {case.id}: {case.title}")
        print(f"  Module: {case.module}")
        print(f"  Risk: {case.risk_class}")
        print(f"  Context keys: {list(case.input_context.keys())}")

    print("\n--- Testing Repair Bench Execution (Mocked) ---")
    bench = RepairBenchService(loader=loader)
    for case in cases:
        result = await bench.run_benchmark_case(case.id)
        if result:
            print(f"[RESULT] {case.id} -> Score: {result.score:.2f}, Success: {result.success}")

    stats = await bench.get_lab_stats()
    print(f"\n[STATS] Final Lab Status: {stats}")

    print("\n--- [PHASE 28] Testing Repair Memory (Learning Loop) ---")
    from services.improve.repair_memory import RepairMemory
    from services.improve.models import RepairMemoryEntry
    memory = RepairMemory()
    
    # 1. Record 2 failures for "radical" strategy in workflow engine
    for _ in range(2):
        memory.record_outcome(RepairMemoryEntry(
            case_id="re-001-replay-bug",
            incident_type="workflow_drift",
            subsystem="libs.workflow.engine",
            patch_strategy="radical",
            outcome="failure",
            score=0.2
        ))
    
    print("\n--- Running re-001 again with failure memory ---")
    result = await bench.run_benchmark_case("re-001-replay-bug")
    # Radical should be penalized now, and logger should show WARNING

    print("\n--- [PHASE 28] Testing Self-Tuning Engine ---")
    from services.improve.self_tuning_engine import SelfTuningEngine
    tuning = SelfTuningEngine(bench_service=bench)
    
    # Simulate a few more runs to get enough data for tuning
    for _ in range(3):
        await bench.run_benchmark_case("re-002-cost-anomaly")
        
    recs = await tuning.generate_recommendations()
    for r in recs:
        print(f"[RECO] {r.parameter_name}: {r.current_value} -> {r.proposed_value}")
        print(f"  Reason: {r.reason}")

if __name__ == "__main__":
    asyncio.run(main())
