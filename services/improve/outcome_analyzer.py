
"""
services/improve/outcome_analyzer.py — Phase 28
Analyzes repair outcomes to detect recurrence and pattern failure.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from libs.db.session import session_scope
from sqlalchemy import select, and_
from libs.db.models.repair_models import RepairMemory as DBMemory
from services.observability.logging import get_logger

logger = get_logger("repair.analyzer")

class OutcomeAnalyzer:
    def __init__(self, recurrence_window_days: int = 7):
        self.recurrence_window = timedelta(days=recurrence_window_days)

    async def detect_recurrence(self) -> List[Dict[str, Any]]:
        """
        Detects if an incident of similar type/subsystem recurred 
        after a supposedly successful repair.
        """
        async with session_scope() as session:
            # Query all memories
            stmt = select(DBMemory).order_by(DBMemory.recorded_at.asc())
            result = await session.execute(stmt)
            memories = result.scalars().all()
            
            recurrences = []
            # For each 'success' repair, check if a later incident happens in the window
            for i, memory in enumerate(memories):
                if memory.outcome != "success":
                    continue
                if not memory.subsystem or not memory.incident_id:
                    continue
                
                # Check subsequent memories for same subsystem
                for later in memories[i+1:]:
                    if not later.subsystem or not later.incident_id:
                        continue
                    time_diff = later.recorded_at - memory.recorded_at
                    if time_diff > self.recurrence_window:
                        break # Out of window
                    
                    if later.subsystem == memory.subsystem and later.incident_id == memory.incident_id:
                        # FOUND A RECURRENCE
                        recurrences.append({
                            "initial_repair_id": memory.memory_id,
                            "recurring_incident_id": later.incident_id,
                            "subsystem": memory.subsystem,
                            "time_to_recur": str(time_diff),
                            "penalty_score": 1.0 - (time_diff.total_seconds() / self.recurrence_window.total_seconds())
                        })
                        logger.warning(f"[RECURRENCE] Detection: Subsystem {memory.subsystem} recurred in {time_diff}")
            
            return recurrences

    async def calculate_subsystem_health(self) -> Dict[str, float]:
        """Calculates a health score per subsystem based on MTTR and Recurrence."""
        async with session_scope() as session:
            stmt = select(DBMemory)
            result = await session.execute(stmt)
            memories = result.scalars().all()
            
            stats = {}
            for m in memories:
                if not m.subsystem:
                    continue
                if m.subsystem not in stats:
                    stats[m.subsystem] = {"success": 0, "total": 0, "recurrences": 0}
                stats[m.subsystem]["total"] += 1
                if m.outcome == "success":
                    stats[m.subsystem]["success"] += 1
            
            # Add recurrence penalty
            recs = await self.detect_recurrence()
            for r in recs:
                if r["subsystem"] in stats:
                    stats[r["subsystem"]]["recurrences"] += 1
            
            health = {}
            for sub, s in stats.items():
                base_rate = s["success"] / s["total"]
                penalty = (s["recurrences"] * 0.2) # 20% penalty per recurrence
                health[sub] = max(0.0, base_rate - penalty)
            
            return health
