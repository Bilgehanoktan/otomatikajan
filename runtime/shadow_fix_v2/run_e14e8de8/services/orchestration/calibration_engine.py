"""
Sovereign AGI — Phase 21 (R-04)
services/orchestration/calibration_engine.py
Forecast vs Actual Calibration & Economic Effectiveness Auditor.
"""
from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ForecastEvent:
    timestamp: float
    project_id: str
    predicted_load: float
    actual_load: Optional[float] = None
    predicted_cost: float = 0.0 # R-08 addition
    actual_cost: float = 0.0    # R-08 addition
    horizon_hours: int = 4

@dataclass
class DecisionEvent:
    timestamp: float
    project_id: str
    action: str # "expand", "shrink", "blocked_by_budget", "blocked_by_ceiling"
    requested_limit: int
    applied_limit: int
    actual_max_load_observed: float = 0.0

@dataclass
class CorrectionEvent:
    timestamp: float
    incident_id: str
    action: str # "proposal", "canary_success", "canary_fail", "rollback", "blocked_by_gate"
    risk_score: float
    is_success: Optional[bool] = None
    severity: str = "medium"

class CalibrationEngine:
    def __init__(self):
        self._forecast_history: List[ForecastEvent] = []
        self._decision_history: List[DecisionEvent] = []
        self._correction_history: List[CorrectionEvent] = []
        self._steering_savings: float = 0.0
        self._total_steered_tasks: int = 0
        self._daily_spend_actuals: Dict[str, float] = {}
        self._daily_spend_forecasts: Dict[str, float] = {}

    def record_forecast(self, project_id: str, predicted: float, predicted_cost: float = 0.0, horizon: int = 4):
        """Logs a prediction to be verified later."""
        self._forecast_history.append(ForecastEvent(
            timestamp=time.time(),
            project_id=project_id,
            predicted_load=predicted,
            predicted_cost=predicted_cost,
            horizon_hours=horizon
        ))
        # Keep window of last 1000 forecasts
        if len(self._forecast_history) > 1000:
            self._forecast_history.pop(0)

    def record_decision(self, project_id: str, action: str, requested: int, applied: int):
        """Logs an adaptive quota decision."""
        self._decision_history.append(DecisionEvent(
            timestamp=time.time(),
            project_id=project_id,
            action=action,
            requested_limit=requested,
            applied_limit=applied
        ))

    def record_steering_impact(self, saved_amount: float):
        """Tracks cumulative savings from economic routing."""
        self._steering_savings += saved_amount
        self._total_steered_tasks += 1

    def update_actuals(self, project_id: str, current_actual_load: float):
        """
        Closes the loop by updating pending forecasts with actual observed load.
        Matches forecasts that were made 'horizon' hours ago (simulated).
        """
        now = time.time()
        for f in self._forecast_history:
            if f.project_id == project_id and f.actual_load is None:
                f.actual_load = current_actual_load
                # Record spend actuals nearby for R-08 calibration
                # In real life, this comes from economic_engine.get_spend_since(timestamp)
                f.actual_cost = getattr(f, "actual_cost", 0.0) + (current_actual_load * 0.005) # Simulated
                break
        
        # Update decisions with max load observed since the decision
        for d in self._decision_history:
            if d.project_id == project_id:
                if current_actual_load > d.actual_max_load_observed:
                    d.actual_max_load_observed = current_actual_load

    def record_correction(self, incident_id: str, action: str, risk_score: float, is_success: Optional[bool] = None, severity: str = "medium"):
        """Logs an autonomous correction/self-healing event."""
        self._correction_history.append(CorrectionEvent(
            timestamp=time.time(),
            incident_id=incident_id,
            action=action,
            risk_score=risk_score,
            is_success=is_success,
            severity=severity
        ))
        if len(self._correction_history) > 500:
            self._correction_history.pop(0)

    def get_calibration_metrics(self) -> Dict[str, Any]:
        """Calculates R-04 and R-05 pillars: Accuracy, Stability, Safety."""
        
        # --- R-04 Forecast Metrics ---
        errors = []
        for f in self._forecast_history:
            if f.actual_load is not None and f.actual_load > 0:
                error = abs(f.predicted_load - f.actual_load) / f.actual_load
                errors.append(error)
        
        avg_forecast_error = (sum(errors) / len(errors)) if errors else 0.0
        
        # --- R-05 Self-Correction Metrics ---
        total_proposals = len([c for c in self._correction_history if c.action == "proposal"]) or 1
        success_patches = len([c for c in self._correction_history if c.action == "canary_success"])
        wrong_patches = len([c for c in self._correction_history if c.action == "canary_fail"])
        
        rollback_events = [c for c in self._correction_history if c.action == "rollback"]
        # A rollback is 'unnecessary' if health didn't improve or it was a false alarm (simulation logic)
        unnecessary_rollbacks = len([r for r in rollback_events if r.is_success == False])
        
        gate_blocks = [c for c in self._correction_history if c.action == "blocked_by_gate"]
        # A block is 'conservative' if risk was high but incident was low severity
        conservative_blocks = len([b for b in gate_blocks if b.risk_score > 0.8 and b.severity == "low"])

        # Economic / Decision Quality (R-04)
        false_expansions = 0
        under_expansions = 0
        for d in self._decision_history:
            if d.action == "expand" and d.actual_max_load_observed <= (d.applied_limit / 1.5):
                false_expansions += 1
            if d.action == "blocked_by_budget" and d.actual_max_load_observed >= d.applied_limit:
                under_expansions += 1
                
        total_decisions = len(self._decision_history) or 1
        
        # --- R-08 Financial Accuracy ---
        cost_errors = []
        for f in self._forecast_history:
            if f.actual_cost > 0:
                cost_error = abs(f.predicted_cost - f.actual_cost) / f.actual_cost
                cost_errors.append(cost_error)
        
        avg_cost_variance = (sum(cost_errors) / len(cost_errors)) if cost_errors else 0.0

        return {
            "r04_forecast_mape": avg_forecast_error,
            "r08_spend_variance_mape": avg_cost_variance, # R-08 Pillar
            "r04_false_expansion_rate": false_expansions / total_decisions,
            "r04_total_steering_savings_usd": self._steering_savings,
            
            "r08_economic_decision_quality": 1.0 - (avg_cost_variance * 0.5 + avg_forecast_error * 0.5),
            
            "r05_patch_success_rate": success_patches / total_proposals,
            "r05_wrong_patch_rate": wrong_patches / total_proposals,
            "r05_unnecessary_rollback_rate": unnecessary_rollbacks / (len(rollback_events) or 1),
            "r05_conservative_block_rate": conservative_blocks / (len(gate_blocks) or 1),
            
            "samples": {
                "forecasts": len(self._forecast_history),
                "decisions": len(self._decision_history),
                "corrections": len(self._correction_history)
            }
        }

# Global Singleton
calibration_engine = CalibrationEngine()
