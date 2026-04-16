"""
Sovereign AGI — Phase 24
services/orchestration/trend_analyzer.py
Predictive Load Forecasting and Capacity Planning.
Analyses historical metrics to anticipate workload spikes.
"""
from __future__ import annotations
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from services.orchestration.calibration_engine import calibration_engine
from services.orchestration.economic_engine import economic_engine

class TrendAnalyzer:
    def __init__(self):
        # In a real system, this would store time-series data or query Prometheus/InfluxDB
        self._history: Dict[str, List[float]] = {} 

    def record_snapshot(self, project_id: str, active_tasks: int):
        """Records a point-in-time snapshot of project load."""
        if project_id not in self._history:
            self._history[project_id] = []
        
        self._history[project_id].append(float(active_tasks))
        # Keep last 100 snapshots
        if len(self._history[project_id]) > 100:
            self._history[project_id].pop(0)

    def forecast_load(self, project_id: str, hours_ahead: int = 4) -> float:
        """
        Calculates the expected load (active tasks) for the future window.
        Uses a Simple Moving Average + Velocity Multiplier.
        """
        project_data = self._history.get(project_id, [0.0])
        if not project_data:
            return 0.0
            
        # Calculate Current Velocity (Change over last 5 points)
        if len(project_data) > 5:
            velocity = (project_data[-1] - project_data[-5]) / 5
        else:
            velocity = 0.0
            
        current_avg = sum(project_data[-10:]) / min(len(project_data), 10)
        
        # Forecast = Current + (Velocity * TimeFactor)
        # We add some jitter for realistic simulation/stress testing
        forecast = current_avg + (velocity * hours_ahead * 1.5)
        
        # Phase 21: Calibration Link (R-04/R-08)
        # Estimate predicted cost for the forecasted window
        # (Assuming nominal regional cost * forecasted load units)
        predicted_cost = forecast * hours_ahead * 0.05 # Simplified model
        
        calibration_engine.record_forecast(
            project_id=project_id, 
            predicted=max(0.0, forecast), 
            predicted_cost=predicted_cost,
            horizon=hours_ahead
        )
        
        return max(0.0, forecast)

    def get_fleet_wide_forecast(self, hours_ahead: int = 4) -> Dict[str, float]:
        """Aggregates forecasts across all known projects."""
        return {pid: self.forecast_load(pid, hours_ahead) for pid in self._history.keys()}

    def get_anomaly_score(self, project_id: str) -> float:
        """Determines if the current load is an outlier (0.0 - 1.0)."""
        project_data = self._history.get(project_id, [])
        if len(project_data) < 20: return 0.0
        
        recent = project_data[-1]
        avg = sum(project_data[:-1]) / len(project_data[:-1])
        
        if avg == 0: return 1.0 if recent > 0 else 0.0
        
        # Deviation ratio
        ratio = recent / avg
        return min(1.0, max(0.0, (ratio - 1.5) / 2.0)) # 1.5x avg starts scoring

# Global Singleton
trend_analyzer = TrendAnalyzer()
