
"""
services/improve/repair_memory.py — Phase 28
Long-term memory for repair outcomes and pattern learning.
"""
from typing import List, Dict, Any, Optional
from services.improve.models import RepairMemoryEntry, PatchPattern
from services.observability.logging import get_logger
from libs.db.session import session_scope
from libs.db.models.repair_models import RepairMemory as DBRepairMemory

logger = get_logger("repair.memory")

class RepairMemory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RepairMemory, cls).__new__(cls)
            cls._instance.entries = []
            cls._instance._initialized = False
        return cls._instance

    async def ensure_initialized(self):
        """Hafızayı veritabanından yükler (Eğer henüz yapılmadıysa)."""
        if self._initialized:
            return

        from libs.db.session import AsyncSessionLocal
        from libs.db.models.repair_models import RepairMemory as DBRepairMemory
        from sqlalchemy import select

        try:
            async with AsyncSessionLocal() as session:
                stmt = select(DBRepairMemory).order_by(DBRepairMemory.recorded_at.desc()).limit(500)
                res = await session.execute(stmt)
                for db_e in res.scalars():
                    # DB modelini Pydantic modeline dönüştür
                    entry = RepairMemoryEntry(
                        id=db_e.memory_id,
                        case_id=db_e.incident_id or "legacy",
                        incident_type=db_e.incident_id or "unknown",
                        subsystem=db_e.subsystem,
                        patch_strategy=db_e.patch_signature.split(":")[-1] if ":" in db_e.patch_signature else db_e.patch_signature,
                        outcome=db_e.outcome,
                        failure_reason=db_e.failure_reason,
                        verifier_rejections=db_e.verifier_rejections or [],
                        score=db_e.score or 0.0,
                        timestamp=db_e.recorded_at
                    )
                    self.entries.append(entry)
            self._initialized = True
            logger.info(f"[MEMORY] Deep memory initialized with {len(self.entries)} historical entries.")
        except Exception as e:
            logger.error(f"Failed to initialize deep memory: {e}")

    def record_outcome(self, entry: RepairMemoryEntry):
        self.entries.append(entry)
        logger.info(f"[MEMORY] Recorded {entry.outcome} for {entry.patch_strategy} in {entry.subsystem}")

        # Fire-and-forget DB persist
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._persist_entry(entry))
        except RuntimeError:
            pass

    def _classify_failure(self, entry: RepairMemoryEntry) -> str:
        """Classifies the failure using a predefined Phase 28 taxonomy."""
        if not entry.verifier_rejections:
            return "unknown_rejection"

        rejections = entry.verifier_rejections
        if "regression" in rejections:
            return "high_regression_risk"
        if "governance" in rejections:
            return "policy_drift_violation"
        if "economic" in rejections:
            return "cost_efficiency_ceiling"
        if "syntax" in rejections or "build" in rejections:
            return "structural_invalidity"
        if "mesh" in rejections or "chaos" in rejections:
            return "distributed_consensus_failure"

        return "multiple_verification_failure"

    async def _persist_entry(self, entry: RepairMemoryEntry):
        try:
            # Apply taxonomy classification (Phase 28 Criterion 5)
            failure_reason = entry.failure_reason
            if entry.outcome == "failure" and not failure_reason:
                failure_reason = self._classify_failure(entry)

            async with session_scope() as session:
                db_entry = DBRepairMemory(
                    memory_id=entry.id,
                    incident_id=entry.incident_type,
                    subsystem=entry.subsystem,
                    patch_signature=f"{entry.subsystem}:{entry.patch_strategy}",
                    outcome=entry.outcome,
                    failure_reason=failure_reason,
                    verifier_rejections=entry.verifier_rejections,
                    score=entry.score,
                    recorded_at=entry.timestamp
                )
                session.add(db_entry)
        except Exception as e:
            logger.error(f"Failed to persist memory entry: {e}")

    def get_pattern_for_strategy(self, strategy: str, subsystem: str) -> PatchPattern:
        """Analyzes history to provide a recommendation for a strategy/subsystem pair."""
        relevant = [e for e in self.entries if e.patch_strategy == strategy and e.subsystem == subsystem]

        if not relevant:
            return PatchPattern(
                pattern_id=f"{strategy}:{subsystem}",
                subsystem=subsystem,
                avg_success_rate=0.5,
                total_attempts=0,
                recommendation="stable"
            )

        successes = sum(1 for e in relevant if e.outcome == "success")
        rate = successes / len(relevant)

        rec = "stable"
        if rate < 0.3 and len(relevant) >= 2: rec = "penalize"
        elif rate > 0.8 and len(relevant) >= 2: rec = "boost"

        return PatchPattern(
            pattern_id=f"{strategy}:{subsystem}",
            subsystem=subsystem,
            avg_success_rate=rate,
            total_attempts=len(relevant),
            recommendation=rec
        )
