"""
Sovereign AGI — Phase 24
services/orchestration/economic_engine.py
Responsible for calculating costs, managing budgets, and estimating burn rates.
"""
from __future__ import annotations
import yaml
import os
from typing import Dict, Any, Optional
from datetime import datetime

class EconomicEngine:
    def __init__(self, policy_path: str = "configs/economic_policy.yaml"):
        self.policy_path = policy_path
        self.policy = self._load_policy()
        self._project_budgets: Dict[str, float] = {} # Simulated in-memory budget cache
        self._spend_history: Dict[str, List[float]] = {} # Historical burn rates for anomaly detection
        self._detailed_attribution: Dict[str, Dict[str, float]] = {} # project -> {metric: value}
        
        # Phase 26: Replenishment Policies
        self.replenishment_configs = {
            0: {"daily_cap": 1000.0, "refill_threshold": 50.0, "max_auto_refill_per_day": 2000.0},
            1: {"daily_cap": 500.0, "refill_threshold": 20.0, "max_auto_refill_per_day": 1000.0},
            2: {"daily_cap": 100.0, "refill_threshold": 5.0, "max_auto_refill_per_day": 200.0},
            3: {"daily_cap": 0.0, "refill_threshold": 0.0, "max_auto_refill_per_day": 0.0}
        }
        self._daily_replenished: Dict[str, float] = {} # project_id -> amount replenished today
        self._current_day = datetime.now().date()

    def _load_policy(self) -> Dict[str, Any]:
        if not os.path.exists(self.policy_path):
            return {
                "regional_base_costs": {"local-node": 0.001},
                "tier_multipliers": {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0}
            }
        with open(self.policy_path, "r") as f:
            return yaml.safe_load(f)

    def calculate_task_cost(self, region: str, isolation_tier: int) -> float:
        """Calculates the estimated cost of a single subtask."""
        base_costs = self.policy.get("regional_base_costs", {})
        multipliers = self.policy.get("tier_multipliers", {})
        
        base = base_costs.get(region, base_costs.get("local-node", 0.001))
        multiplier = multipliers.get(isolation_tier, 1.0)
        
        return base * multiplier

    def is_budget_sufficient(self, project_id: str, threshold: float = 0.0) -> bool:
        """
        Checks if the project has enough budget to continue.
        In production, this would query the DB (current_budget_usd).
        """
        # Placeholder for DB check
        budget = self._project_budgets.get(project_id, 100.0) # Default for simulation
        return budget > threshold

    def record_spend(self, project_id: str, amount: float, region: str, tier: int):
        """Deducts spend and updates attribution maps."""
        if project_id not in self._project_budgets:
            self._project_budgets[project_id] = 100.0
        
        self._project_budgets[project_id] -= amount
        
        # Attribution tracking
        if project_id not in self._detailed_attribution:
            self._detailed_attribution[project_id] = {"total": 0.0, f"region_{region}": 0.0, f"tier_{tier}": 0.0}
        
        self._detailed_attribution[project_id]["total"] += amount
        self._detailed_attribution[project_id][f"region_{region}"] = self._detailed_attribution[project_id].get(f"region_{region}", 0.0) + amount
        self._detailed_attribution[project_id][f"tier_{tier}"] = self._detailed_attribution[project_id].get(f"tier_{tier}", 0.0) + amount

        # Track burn rate history (simulated window)
        if project_id not in self._spend_history:
            self._spend_history[project_id] = []
        self._spend_history[project_id].append(amount)
        if len(self._spend_history[project_id]) > 50:
            self._spend_history[project_id].pop(0)

    def apply_replenishment_policy(self, project_id: str, tier: int) -> float:
        """Phase 26: Autonomously tops up budget if eligible, with safety caps."""
        # Reset counters if day changed
        today = datetime.now().date()
        if today > self._current_day:
            self._daily_replenished = {}
            self._current_day = today

        config = self.replenishment_configs.get(tier)
        if not config or config["daily_cap"] <= 0: return 0.0
        
        current = self._project_budgets.get(project_id, 0.0)
        daily_used = self._daily_replenished.get(project_id, 0.0)

        if current < config["refill_threshold"]:
            if daily_used >= config["max_auto_refill_per_day"]:
                # Limit hit! This requires manual recovery (R-08)
                return -1.0 

            refill_needed = config["daily_cap"] - current
            # Don't exceed daily auto-refill quota
            refill_amount = min(refill_needed, config["max_auto_refill_per_day"] - daily_used)
            
            self._project_budgets[project_id] = current + refill_amount
            self._daily_replenished[project_id] = daily_used + refill_amount
            return refill_amount
        return 0.0

    def trigger_budget_recovery(self, project_id: str) -> Dict[str, Any]:
        """
        R-08: Emergency flows when budget is exhausted and auto-refill is capped.
        Options: downgrade tier, force cheap regions, or freeze fleet expansion.
        """
        return {
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "status": "RECOVERY_INITIATED",
            "actions_taken": [
                "FORCED_REGION_STEERING_LOW_COST",
                "QUOTA_EXPANSION_LOCKED",
                "TIER_DOWNGRADE_ADVISORY"
            ]
        }

    def detect_spend_anomaly(self, project_id: str) -> Dict[str, Any]:
        """
        R-08: Determines if the project is spending significantly faster than average.
        Returns a rich status instead of just a raw float.
        """
        history = self._spend_history.get(project_id, [])
        if len(history) < 20: return {"score": 0.0, "reason": "insufficient_data"}
        
        # Windowed analysis (last 5 vs previous 15)
        recent_window = history[-5:]
        avg_baseline = sum(history[:-5]) / len(history[:-5])
        avg_recent = sum(recent_window) / len(recent_window)
        
        if avg_baseline == 0: 
            return {"score": 1.0, "reason": "spike_from_zero"} if avg_recent > 1.0 else {"score": 0.0, "reason": "normal"}
        
        ratio = avg_recent / avg_baseline
        # Anomaly score: 0.0 to 1.0 (Starts scoring at 2.5x average)
        score = min(1.0, max(0.0, (ratio - 2.5) / 5.0))
        
        return {
            "score": score,
            "ratio": ratio,
            "reason": "burn_rate_spike" if score > 0.5 else "normal",
            "avg_baseline": avg_baseline,
            "avg_recent": avg_recent,
            "is_critical": score > 0.7
        }

    def get_region_cost_score(self, region: str) -> float:
        """
        Returns a score (0.0 to 1.0) where 1.0 is cheapest.
        Used by MeshRouter for economic steering.
        """
        base_costs = self.policy.get("regional_base_costs", {})
        costs = list(base_costs.values())
        if not costs: return 1.0
        
        min_cost = min(costs)
        max_cost = max(costs)
        current = base_costs.get(region, max_cost)
        
        if max_cost == min_cost: return 1.0
        
        # Invert: Higher cost = Lower score
        return (max_cost - current) / (max_cost - min_cost)

# Global Singleton
economic_engine = EconomicEngine()
