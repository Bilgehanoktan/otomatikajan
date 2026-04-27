import time
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import GovernorDomain
from libs.db.repositories.governor_resilience_repository import GovernorSloRepo

class GovernorSloMonitor:
    """Governor operasyonlarının performans (SLO) ölçümünü yapar."""
    
    # Hedefler (ms)
    SLO_TARGETS = {
        "decision": 300,
        "meta_resolve": 500,
        "execution": 700,
        "conflict_resolve": 1000
    }

    @staticmethod
    async def record_latency(
        db: AsyncSession, 
        domain: GovernorDomain, 
        operation: str, 
        latency_ms: int, 
        success: bool = True
    ):
        await GovernorSloRepo.save_slo_sample(db, domain, operation, latency_ms, success)
        
        # SLO İhlali kontrolü
        target = GovernorSloMonitor.SLO_TARGETS.get(operation, 2000)
        if latency_ms > target:
            # Opsiyonel: Alert fırlat veya Lineage'a yaz
            pass

    @staticmethod
    async def get_performance_summary(db: AsyncSession, domain: GovernorDomain) -> Dict[str, Any]:
        samples = await GovernorSloRepo.list_recent_slo(db, domain, limit=50)
        if not samples:
            return {"status": "NO_DATA"}
            
        latencies = [s.latency_ms for s in samples]
        avg_latency = sum(latencies) / len(latencies)
        success_rate = sum(1 for s in samples if s.success) / len(samples)
        
        return {
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
            "success_rate": round(success_rate * 100, 2),
            "sample_count": len(samples)
        }
