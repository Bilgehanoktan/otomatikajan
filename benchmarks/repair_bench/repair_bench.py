import asyncio
import logging
import time
from typing import List, Dict, Any
from benchmarks.repair_bench.benchmark_loader import BenchmarkLoader, RepairScenario
from services.repair.repair_orchestrator import RepairOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("repair_bench.engine")

class RepairBench:
    """The Scientific Execution Engine for Repair Benchmarks."""
    
    def __init__(self, loader: BenchmarkLoader):
        self.loader = loader
        self.orchestrator = RepairOrchestrator()
        self.results = []

    async def run_suite(self, scenario_ids: List[str] = None):
        """Runs the benchmark suite against selected scenarios."""
        ids = scenario_ids or self.loader.list_scenarios()
        logger.info(f"Starting Benchmark Suite: {len(ids)} scenarios found.")
        
        for sid in ids:
            scenario = self.loader.load_scenario(sid)
            if not scenario:
                continue
            
            result = await self.run_scenario(scenario)
            self.results.append(result)
            
        self.print_summary()

    async def run_scenario(self, scenario: RepairScenario) -> Dict[str, Any]:
        """Executes a single repair scenario in SHADOW mode."""
        logger.info(f"--- Running Scenario: {scenario.scenario_id} [{scenario.name}] ---")
        start_time = time.time()
        
        # Trigger Repair Orchestrator in SHADOW mode (Phase 28 requirement)
        # We assume orchestrator has a method for this or we adapt its flow
        outcome = await self.orchestrator.shadow_repair_cycle(
            incident_type=scenario.incident_type,
            payload=scenario.payload
        )
        
        latency = (time.time() - start_time) * 1000
        
        # evaluation logic (placeholder for Phase 28 Stage 2)
        success = outcome.get("status") == scenario.expected_outcome
        
        return {
            "scenario_id": scenario.scenario_id,
            "success": success,
            "latency_ms": round(latency, 2),
            "candidates_generated": outcome.get("candidates_count", 0),
            "winner_score": outcome.get("winning_score", 0),
            "outcome_summary": outcome.get("summary", "N/A")
        }

    def print_summary(self):
        """Prints the scientific summary of the benchmark run."""
        total = len(self.results)
        if total == 0:
            print("\n[!] No results to summarize.")
            return

        successes = sum(1 for r in self.results if r["success"])
        avg_latency = sum(r["latency_ms"] for r in self.results) / total
        
        print("\n" + "="*50)
        print(f" PHASE 28 REPAIR BENCHMARK SUMMARY ")
        print("="*50)
        print(f" Total Scenarios  : {total}")
        print(f" Success Rate     : {(successes/total)*100:.2f}% ({successes}/{total})")
        print(f" Avg Latency      : {avg_latency:.2f} ms")
        print(f" Tournament Qual  : {sum(r['candidates_generated'] for r in self.results)/total:.1f} candidates/avg")
        print("="*50 + "\n")

if __name__ == "__main__":
    loader = BenchmarkLoader()
    bench = RepairBench(loader)
    asyncio.run(bench.run_suite())
