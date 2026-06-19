import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from libs.db.models.ui_repair_models import UICausalMemory, IncidentPatternType

logger = logging.getLogger(__name__)

class CausalMemoryEngine:
    """Engine for storing and retrieving long-term causal knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_outcome(
        self,
        memory_key: str,
        pattern_type: str,
        root_cause: str,
        trigger_conditions: Dict[str, Any],
        action_taken: Dict[str, Any],
        outcome: Dict[str, Any],
        success_score: float,
        confidence: float = 1.0
    ) -> UICausalMemory:
        """Records a causal event and its outcome, updating if the key exists."""
        
        stmt = select(UICausalMemory).where(UICausalMemory.memory_key == memory_key)
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        
        if existing:
            # Update existing entry with incremental learning
            existing.recurrence_count += 1
            # Simple weighted average for success score
            existing.success_score = (existing.success_score * (existing.recurrence_count - 1) + success_score) / existing.recurrence_count
            existing.last_seen_at = datetime.now(timezone.utc)
            existing.outcome_json = outcome # Update with latest outcome
            existing.confidence = (existing.confidence + confidence) / 2
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new memory entry
            memory = UICausalMemory(
                memory_key=memory_key,
                pattern_type=pattern_type,
                root_cause=root_cause,
                trigger_conditions_json=trigger_conditions,
                action_taken_json=action_taken,
                outcome_json=outcome,
                success_score=success_score,
                confidence=confidence,
                recurrence_count=1,
                last_seen_at=datetime.now(timezone.utc)
            )
            self.db.add(memory)
            await self.db.commit()
            await self.db.refresh(memory)
            return memory

    async def get_best_remediation(self, root_cause: str) -> Optional[Dict[str, Any]]:
        """Retrieves the most successful remediation action for a given root cause."""
        # Simplified fuzzy match on root cause string for now
        stmt = select(UICausalMemory).where(
            UICausalMemory.root_cause.ilike(f"%{root_cause}%"),
            UICausalMemory.success_score >= 0.7
        ).order_by(UICausalMemory.success_score.desc()).limit(1)
        
        res = await self.db.execute(stmt)
        memory = res.scalar_one_or_none()
        
        if memory:
            return {
                "action": memory.action_taken_json,
                "expected_success": memory.success_score,
                "confidence": memory.confidence,
                "historical_recurrence": memory.recurrence_count
            }
        return None
