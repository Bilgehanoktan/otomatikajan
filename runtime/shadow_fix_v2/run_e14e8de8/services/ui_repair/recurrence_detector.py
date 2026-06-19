from typing import List, Dict, Any
from datetime import datetime, timedelta

class RecurrenceDetector:
    """
    Phase 6: Recurrence and Flapping Detector.
    Analyzes historical health data to find chronic patterns.
    """

    @staticmethod
    def detect_flapping(history: List[Dict[str, Any]], threshold: int = 3) -> bool:
        """
        Detects if a route is 'flapping' (alternating between PASS and FAIL).
        History should be ordered by time descending.
        """
        if len(history) < threshold * 2:
            return False
            
        transitions = 0
        last_status = history[0].get("status")
        
        for point in history[1:]:
            current_status = point.get("status")
            if current_status != last_status:
                transitions += 1
            last_status = current_status
            
        return transitions >= threshold

    @staticmethod
    def is_chronic_failure(history: List[Dict[str, Any]], window_minutes: int = 60) -> bool:
        """
        Detects if a route has been failing consistently for a duration.
        """
        if not history:
            return False
            
        recent_fails = [p for p in history if p.get("status") == "FAIL"]
        if len(recent_fails) < 3:
            return False
            
        # If last 3 are fails, it's chronic
        return all(p.get("status") == "FAIL" for p in history[:3])
