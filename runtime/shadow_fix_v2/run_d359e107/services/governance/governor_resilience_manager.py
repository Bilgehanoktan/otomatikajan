from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import GovernorDomain, GovernorRuntimeStatus
from libs.db.repositories.governor_resilience_repository import GovernorResilienceRepo

class GovernorResilienceManager:
    """Governor domain sağlığını ve çalışma modlarını yönetir."""
    
    @staticmethod
    async def mark_healthy(db: AsyncSession, domain: GovernorDomain):
        await GovernorResilienceRepo.upsert_runtime_status(
            db, domain, GovernorRuntimeStatus.HEALTHY, reason="Self-healing check passed"
        )

    @staticmethod
    async def mark_failure(db: AsyncSession, domain: GovernorDomain, reason: str):
        record = await GovernorResilienceRepo.get_runtime_status(db, domain)
        new_status = GovernorRuntimeStatus.DEGRADED
        
        if record and record.failure_count >= 5:
            new_status = GovernorRuntimeStatus.FAILED
            
        await GovernorResilienceRepo.upsert_runtime_status(
            db, domain, new_status, reason=reason
        )

    @staticmethod
    async def should_isolate_domain(db: AsyncSession, domain: GovernorDomain) -> bool:
        record = await GovernorResilienceRepo.get_runtime_status(db, domain)
        if record and record.runtime_status in [GovernorRuntimeStatus.FAILED, GovernorRuntimeStatus.ISOLATED]:
            return True
        return False

    @staticmethod
    async def get_all_runtime_status(db: AsyncSession) -> List[Dict[str, Any]]:
        # Tüm domainler için durum listesi (basitleştirilmiş)
        results = []
        for domain in GovernorDomain:
            record = await GovernorResilienceRepo.get_runtime_status(db, domain)
            if record:
                results.append({
                    "domain": domain.value,
                    "status": record.runtime_status.value,
                    "failure_count": record.failure_count,
                    "advisory_only": bool(record.advisory_only)
                })
        return results

    @staticmethod
    async def set_freeze_mode(db: AsyncSession, domain: GovernorDomain, frozen: bool):
        await GovernorResilienceRepo.upsert_runtime_status(
            db, domain, 
            GovernorRuntimeStatus.FROZEN if frozen else GovernorRuntimeStatus.HEALTHY,
            freeze_mode=1 if frozen else 0
        )
