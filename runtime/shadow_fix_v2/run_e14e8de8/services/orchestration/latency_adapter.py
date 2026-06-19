"""
Sovereign AGI — Phase 20
services/orchestration/latency_adapter.py
Provides latency metrics for cross-regional mesh routing.
"""
from __future__ import annotations
import random
import time
from typing import Dict, Optional

from services.orchestration.mesh_state_store import mesh_state_store

class LatencyAdapter:
    """
    Adapter to fetch or simulate cross-regional network performance.
    In a real production environment, this would query a metrics provider (e.g., CloudWatch, Prometheus).
    """
    def __init__(self):
        # Default Baseline Matrix (Source -> Target: ms)
        self.baseline_matrix = {
            "us-east-1": {"eu-central-1": 85.0, "ap-southeast-1": 195.0, "us-east-1": 5.0},
            "eu-central-1": {"us-east-1": 88.0, "ap-southeast-1": 160.0, "eu-central-1": 5.0},
            "ap-southeast-1": {"us-east-1": 200.0, "eu-central-1": 155.0, "ap-southeast-1": 10.0},
        }

    async def get_latency(self, source_region: str, target_region: str) -> float:
        """
        Returns the current latency between two regions.
        Includes a 'Simulation Jitter' and PERSISTS the result for mesh-wide visibility.
        """
        # 1. Baseline logic
        base = self.baseline_matrix.get(source_region, {}).get(target_region)
        if base is None:
            if source_region == target_region: base = 5.0
            else: return 500.0

        # 2. Apply jitter
        jitter = random.uniform(-2.0, 5.0)
        current_val = max(5.0, base + jitter)

        # 3. PERSISTENCE (Phase 20 Stage 3)
        # We record this 'Observation' into the global mesh state
        mesh_state_store.set_region_metrics(target_region, {
            f"latency_from_{source_region}": current_val,
            "last_latency_check": time.time()
        })
        
        return current_val

    async def get_health_score(self, region_id: str) -> float:
        """Provides a 0.0 to 1.0 health score and PERSISTS it."""
        score = 1.0
        if region_id == "ap-southeast-1": score = 0.85
        
        mesh_state_store.set_region_metrics(region_id, {"health_score": score})
        return score

latency_adapter = LatencyAdapter()
