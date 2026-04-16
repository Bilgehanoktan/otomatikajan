"""
Sovereign AGI — Phase 25
services/orchestration/adaptive_quota_adjuster.py
Autonomous Elasticity Engine.
Adjusts concurrency limits based on TrendAnalyzer forecasts and Economic policies.
"""
from __future__ import annotations
import math
from services.orchestration.fleet_manager import fleet_manager
from services.orchestration.trend_analyzer import trend_analyzer
from services.orchestration.economic_engine import economic_engine
from services.orchestration.calibration_engine import calibration_engine

class AdaptiveQuotaAdjuster:
    def __init__(self):
        # Configuration for expansion aggressiveness
        self.tier_strategies = {
            0: {"headroom": 1.5, "min_budget_percent": 0.1}, # Tier 0: 50% extra headroom
            1: {"headroom": 1.2, "min_budget_percent": 0.2}, 
            2: {"headroom": 1.1, "min_budget_percent": 0.3},
            3: {"headroom": 1.0, "min_budget_percent": 0.5}  # Tier 3: No extra headroom
        }
        self.max_expansion_multiplier = 2.0 # Hard Ceiling: 2x base limit

    def run_adjustment_cycle(self):
        """
        Iterates through the fleet and performs adaptive quota re-balancing.
        Usually called by a background heartbeat or post-task-burst event.
        """
        stats = fleet_manager.get_fleet_stats()
        for project_id in stats["high_load_projects"]:
            self._adjust_project(project_id)

    def _adjust_project(self, project_id: str):
        snapshot = fleet_manager._active_workloads.get(project_id)
        if not snapshot: return

        # 1. Get Forecast for next 4 hours
        forecast = trend_analyzer.forecast_load(project_id, hours_ahead=4)
        
        # 2. Apply Tier Strategy
        strategy = self.tier_strategies.get(snapshot.isolation_tier, self.tier_strategies[2])
        target_limit = math.ceil(forecast * strategy["headroom"])
        
        # 3. Ensure we don't drop below base limit (preservation)
        target_limit = max(target_limit, snapshot.base_concurrency_limit)
        
        # 4. Apply Hard Ceiling (Safety Gate)
        hard_ceiling = snapshot.base_concurrency_limit * self.max_expansion_multiplier
        target_limit = min(target_limit, int(hard_ceiling))

        # 5. Economic Coupling: Block expansion if budget is too low
        # In simulation, we assume budget check is sufficient
        action = "none"
        if target_limit > snapshot.concurrency_limit:
            if not economic_engine.is_budget_sufficient(project_id, threshold=1.0):
                # Budget too low for expansion, stay at current limit or base
                action = "blocked_by_budget"
                target_limit = snapshot.concurrency_limit
            else:
                action = "expand"
        elif target_limit < snapshot.concurrency_limit:
            action = "shrink"

        # Phase 21: Calibration Link (R-04)
        if action != "none":
            calibration_engine.record_decision(
                project_id=project_id,
                action=action,
                requested=target_limit if action != "blocked_by_budget" else target_limit + 10, # simulated request
                applied=target_limit
            )

        # 6. Push to FleetManager
        if target_limit != snapshot.concurrency_limit:
            fleet_manager.update_concurrency_limit(project_id, target_limit)

# Global Singleton
adaptive_quota_adjuster = AdaptiveQuotaAdjuster()
