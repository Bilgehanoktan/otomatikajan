"""
Sovereign AGI — Phase 18
services/governance/emergency_policy.py
Policy Engine for Emergency Autonomy & Safety Reflexes.
"""
from __future__ import annotations
import os
import yaml
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class EmergencyState(Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    SAFETY_FREEZE = "SAFETY_FREEZE"
    QUARANTINE = "QUARANTINE"
    READ_ONLY = "READ_ONLY"

class EmergencyPolicyEngine:
    def __init__(self, policy_path: str = "configs/emergency_policy.yaml", threshold_path: str = "configs/incident_thresholds.yaml"):
        self.policy_path = policy_path
        self.threshold_path = threshold_path
        self.policies = self._load_yaml(policy_path)
        self.thresholds = self._load_yaml(threshold_path)
        self.active_emergencies: Dict[str, EmergencyState] = {}

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    async def evaluate_risk(self, metrics: Dict[str, Any]) -> EmergencyState:
        """Evaluate current system health against thresholds and return required state."""
        # 1. Check Error Rate (P0/P1)
        error_rate = metrics.get("error_rate", 0)
        t_error = self.thresholds.get("thresholds", {}).get("error_rate_spike", {})
        
        if error_rate >= t_error.get("p0", 0.20):
            return EmergencyState.SAFETY_FREEZE
        if error_rate >= t_error.get("p1", 0.05):
            return EmergencyState.DEGRADED

        # 2. Check Budget/Cost (P1 Quarantine)
        cost_proj = metrics.get("cost_projection", 0)
        t_cost = self.thresholds.get("thresholds", {}).get("budget_protection", {})
        if cost_proj >= t_cost.get("p1", 500):
            return EmergencyState.QUARANTINE

        # 3. Check Latency (Degraded/Fallback)
        latency = metrics.get("latency_p95", 0)
        t_latency = self.thresholds.get("thresholds", {}).get("latency_degradation", {})
        if latency >= t_latency.get("p1", 5000):
            return EmergencyState.READ_ONLY
        
        return EmergencyState.NORMAL

    def get_action_for_state(self, state: EmergencyState) -> Dict[str, Any]:
        """Get the specific technical response for a given state from policy config."""
        mode_key = state.value.lower()
        return self.policies.get("emergency_modes", {}).get(mode_key, {"action": "NONE"})

    async def should_block_action(self, action_type: str, current_metrics: Dict[str, Any]) -> bool:
        """High-level safety gate: True if the action should be blocked due to emergency."""
        state = await self.evaluate_risk(current_metrics)
        
        if state == EmergencyState.SAFETY_FREEZE:
            return True # Block everything except rollbacks (handled by engine)
            
        if state == EmergencyState.QUARANTINE and action_type == "external_tool":
            return True
            
        if state == EmergencyState.READ_ONLY and action_type == "db_write":
            return True
            
        return False
