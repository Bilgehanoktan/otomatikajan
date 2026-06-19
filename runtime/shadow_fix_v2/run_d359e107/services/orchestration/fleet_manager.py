"""
Sovereign AGI — Phase 23
services/orchestration/fleet_manager.py
Manages the global state of all projects (The Fleet) across the mesh.
Tracks quotas, concurrency, and priority-based preemption.
"""
from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.orchestration.economic_engine import economic_engine
from services.orchestration.trend_analyzer import trend_analyzer
from services.orchestration.calibration_engine import calibration_engine
from libs.mesh.state_fabric import state_fabric

class ProjectSnapshot(BaseModel):
    project_id: str
    active_tasks: int
    concurrency_limit: int
    base_concurrency_limit: int = 0
    last_adjustment_time: float = 0.0
    priority: str
    isolation_tier: int
    health: str
    burn_rate: float = 0.0
    forecast_load: float = 0.0

class FleetManager:
    def __init__(self):
        # In a real distributed system, this would be backed by Redis or the MeshStateStore
        self._active_workloads: Dict[str, ProjectSnapshot] = {}
        self._tier_usage: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}

    def register_workload(self, project_id: str, tier: int, priority: str, limit: int):
        if project_id not in self._active_workloads:
            self._active_workloads[project_id] = ProjectSnapshot(
                project_id=project_id,
                active_tasks=0,
                concurrency_limit=limit,
                base_concurrency_limit=limit,
                last_adjustment_time=time.time(),
                priority=priority,
                isolation_tier=tier,
                health="NOMINAL",
                burn_rate=0.0,
                forecast_load=0.0
            )

    def update_concurrency_limit(self, project_id: str, new_limit: int):
        """Updates the live limit, enforcing a minimal quiet period between changes."""
        if project_id in self._active_workloads:
            snapshot = self._active_workloads[project_id]
            now = time.time()
            # 60 second cooling period to prevent thrashing
            if now - snapshot.last_adjustment_time > 60:
                snapshot.concurrency_limit = new_limit
                snapshot.last_adjustment_time = now

    def increment_task(self, project_id: str, region: str = "local-node") -> bool:
        """Increments task count if quota AND budget allow."""
        if project_id not in self._active_workloads:
            return False
        
        snapshot = self._active_workloads[project_id]
        
        # ── Faz 24: Economic & Budget Check ──
        if not economic_engine.is_budget_sufficient(project_id):
            snapshot.health = "BUDGET_EXHAUSTED"
            return False

        if snapshot.active_tasks >= snapshot.concurrency_limit:
            # Check if we can preempt a lower tier workload (Phase 23 Policy)
            return self._attempt_preemption(snapshot.isolation_tier)
            
        # Success: Increment and record economic impact
        snapshot.active_tasks += 1
        self._tier_usage[snapshot.isolation_tier] += 1
        
        # Record Spend (Phase 26: Detailed Attribution)
        cost = economic_engine.calculate_task_cost(region, snapshot.isolation_tier)
        economic_engine.record_spend(project_id, cost, region, snapshot.isolation_tier)
        
        # Update Forecasting & Burn Rate
        trend_analyzer.record_snapshot(project_id, snapshot.active_tasks)
        calibration_engine.update_actuals(project_id, snapshot.active_tasks)
        
        snapshot.forecast_load = trend_analyzer.forecast_load(project_id)
        snapshot.burn_rate = snapshot.active_tasks * cost * 3600 # Est $/hr
        
        return True

    def decrement_task(self, project_id: str):
        if project_id in self._active_workloads:
            snapshot = self._active_workloads[project_id]
            if snapshot.active_tasks > 0:
                snapshot.active_tasks -= 1
                self._tier_usage[snapshot.isolation_tier] -= 1

    def get_fleet_stats(self) -> Dict[str, Any]:
        return {
            "total_projects": len(self._active_workloads),
            "tier_usage": self._tier_usage,
            "high_load_projects": [p for p, s in self._active_workloads.items() if s.active_tasks > 0],
            "all_project_ids": list(self._active_workloads.keys())
        }

    def perform_governance_cycle(self):
        """Phase 26: Periodic check for budget replenishment and anomalies."""
        for project_id, snapshot in self._active_workloads.items():
            # 1. Budget Replenishment (R-08: Handle exhaustion vs limits)
            replenished = economic_engine.apply_replenishment_policy(project_id, snapshot.isolation_tier)
            if replenished == -1.0:
                # Limit hit! Auto-refill cannot continue. Trigger recovery.
                snapshot.health = "BUDGET_EXHAUSTED_LOCKED"
                economic_engine.trigger_budget_recovery(project_id)
            elif replenished > 0:
                snapshot.health = "NOMINAL" # Reset health if refilled
            
            # 2. Anomaly Detection (R-08: Process rich anomaly report)
            anomaly_report = economic_engine.detect_spend_anomaly(project_id)
            score = anomaly_report.get("score", 0.0)
            
            if score > 0.7:
                snapshot.health = "SPEND_ANOMALY"
            elif snapshot.health == "SPEND_ANOMALY" and score < 0.3:
                snapshot.health = "NOMINAL"

    async def sync_mesh_state(self, region_id: str):
        """Phase 27: Persistent synchronization with the GlobalStateFabric."""
        for project_id, snapshot in self._active_workloads.items():
            await state_fabric.put_project_snapshot(project_id, snapshot.model_dump())
        
        # Log localized summary to fabric as well
        stats = self.get_fleet_stats()
        await state_fabric.put_region_state(region_id, {
            "stats": stats,
            "timestamp": time.time()
        })

    def _attempt_preemption(self, target_tier: int) -> bool:
        """
        Placeholder for preemption logic. 
        In Phase 23, if a Tier-0 project needs capacity, we could signal 
        a Tier-3 project to pause.
        """
        # For now, we remain conservative
        return False

# Global Instance
fleet_manager = FleetManager()
