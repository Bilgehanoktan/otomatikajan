import os
from benchmarks.repair_bench.benchmark_loader import BenchmarkLoader

loader = BenchmarkLoader()
scenarios = loader.list_scenarios()
print(f"Total scenarios found: {len(scenarios)}")
print(f"Scenarios: {scenarios}")

for sid in scenarios:
    s = loader.load_scenario(sid)
    if s:
        print(f"Loaded {sid} success")
    else:
        print(f"Failed to load {sid}")
