import logging
from libs.db.models.governance_models import GovernorRuntimeStatus, GovernorDomain
from libs.db.repositories.governor_repository import GovernorRuntimeRepo
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class GovernorPolicyFreeze:
    @staticmethod
    async def is_policy_evolution_frozen(db: AsyncSession) -> bool:
        """Sistem kilitli mi kontrol eder (Resilience/Drill durumları)."""
        # Meta veya Policy domain'lerinden biri FROZEN ise izin verme
        for domain in [GovernorDomain.META, GovernorDomain.POLICY]:
            status = await GovernorRuntimeRepo.get_status(db, domain)
            if status and status.runtime_status == GovernorRuntimeStatus.FROZEN:
                return True
        return False

    @staticmethod
    async def ensure_not_frozen(db: AsyncSession):
        if await GovernorPolicyFreeze.is_policy_evolution_frozen(db):
            raise Exception("POLICY_EVOLUTION_LOCKED: System is in FROZEN state or active DRILL.")
