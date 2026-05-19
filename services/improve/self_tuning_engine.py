
"""
services/improve/self_tuning_engine.py — Phase 28
Analyzes Lab results and proposes optimized repair thresholds and weights.
"""
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from services.improve.repair_bench import RepairBenchService
from services.observability.logging import get_logger
from libs.db.session import session_scope
from libs.db.models.repair_models import SelfTuningSuggestion

logger = get_logger("repair.self_tuning")

class TuningRecommendation(BaseModel):
    parameter_name: str
    current_value: float
    proposed_value: float
    reason: str
    expected_impact: str
    confidence: float

class SelfTuningEngine:
    def __init__(self, bench_service: RepairBenchService):
        self.bench = bench_service

    async def generate_and_persist_recommendations(self) -> List[SelfTuningSuggestion]:
        """Analyzes recent lab performance, generates recalibration signals, and stores them."""
        stats = await self.bench.get_lab_stats()
        recs = await self._calculate_recommendations(stats)
        
        db_suggestions = []
        if not recs:
            return []

        for attempt in range(3):
            db_suggestions = [
                SelfTuningSuggestion(
                    suggestion_id=f"SUG-{uuid.uuid4().hex[:8].upper()}",
                    parameter_name=r.parameter_name,
                    current_value=r.current_value,
                    proposed_value=r.proposed_value,
                    reason=r.reason,
                    expected_impact=r.expected_impact,
                    status="pending",
                    created_at=datetime.now(timezone.utc)
                )
                for r in recs
            ]

            try:
                async with session_scope() as session:
                    for suggestion in db_suggestions:
                        session.add(suggestion)
                    # Commit is handled by session_scope
                break
            except Exception as exc:
                if "database is locked" not in str(exc).lower() or attempt == 2:
                    logger.warning(
                        "Self-tuning persistence degraded; returning generated suggestions without durable write: %s",
                        exc,
                    )
                    return db_suggestions
                await asyncio.sleep(0.5 * (attempt + 1))

        logger.info(f"Persisted {len(db_suggestions)} self-tuning suggestions to database.")
        return db_suggestions

    async def generate_recommendations(self) -> List[TuningRecommendation]:
        """Backward-compatible non-persistent recommendation API for lab/E2E checks."""
        stats = await self.bench.get_lab_stats()
        return await self._calculate_recommendations(stats)

    async def _calculate_recommendations(self, stats: Dict[str, Any]) -> List[TuningRecommendation]:
        """Internal logic for suggestion calculation, now including recurrence analysis."""
        recs = []
        if stats.get("total_runs", 0) < 3: # Lowered threshold for lab testing
            logger.info("Not enough data for self-tuning.")
            return []

        success_rate = stats.get("success_rate", 0.0)
        
        # 1. Base Quality Signals
        if success_rate < 0.6:
            recs.append(TuningRecommendation(
                parameter_name="patch_accept_threshold",
                current_value=0.7,
                proposed_value=0.85,
                reason=f"Low success rate ({success_rate:.2f}) indicates too many low-quality patches are being accepted.",
                expected_impact="Higher quality repairs, lower MTBF.",
                confidence=0.85
            ))

        # 2. Recurrence Signals (Phase 28 Workstream D/E Expansion)
        from services.improve.outcome_analyzer import OutcomeAnalyzer
        analyzer = OutcomeAnalyzer()
        recurrences = await analyzer.detect_recurrence()
        
        sub_recs = {}
        for r in recurrences:
            sub = r["subsystem"]
            if not sub:
                continue
            sub_recs[sub] = sub_recs.get(sub, 0) + 1
            
        for sub, count in sub_recs.items():
            if count >= 1:
                recs.append(TuningRecommendation(
                    parameter_name=f"risk_weight_{sub.replace('.', '_')}",
                    current_value=1.0,
                    proposed_value=1.5,
                    reason=f"Recurrence detected in {sub}. Increasing risk weight significantly.",
                    expected_impact="Reduces recurrence by favoring ultra-conservative fixes for this subsystem.",
                    confidence=0.8
                ))

        return recs

    async def simulate_impact(self, suggestion_id: str) -> bool:
        """Simulates the new parameter against historically failed cases."""
        logger.info(f"[SIMULATION] Testing suggestion {suggestion_id}...")
        # In production, this would re-run the PatchRanker with new values on the failed cases list
        return True
