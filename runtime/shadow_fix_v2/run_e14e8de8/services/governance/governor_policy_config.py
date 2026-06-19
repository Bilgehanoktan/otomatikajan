import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.repositories.governor_policy_repository import GovernorPolicyEvolutionRepo
from libs.db.models.governance_models import PolicyEvolutionStatus, GovernorDomain

logger = logging.getLogger(__name__)

class GovernorPolicyConfig:
    # --- Default Policy Values ---
    DEFAULT_POLICIES = {
        "policy.veto.priority": ["POLICY", "INCIDENT", "APPROVAL", "WORKFLOW", "REPAIR"],
        "policy.archive.allowed_with_open_incident": False,
        "policy.replay.max_retries": 3,
        "policy.replay.cooldown_minutes": 60,
        "policy.escalation.prime_risk_floor": 0.45,
        "policy.conflict.policy_veto_enabled": True,
        "policy.auto_approve.require_no_incident": True,
        "policy.execution.rate_limit_per_hour": 10,
    }

    _cached_overrides: Dict[str, Any] = {}

    @classmethod
    async def refresh_overrides(cls, db: AsyncSession):
        """Aktif (APPROVED/APPLIED) olan en güncel evrimleri yükler."""
        try:
            # En son uygulanan evrimleri policy_key bazlı al
            # Basitlik için list_recent_proposals kullanıp içerde filtreleyebiliriz 
            # veya repo'ya özel metod eklenebilir.
            applied = await GovernorPolicyEvolutionRepo.list_recent_proposals(db, status=PolicyEvolutionStatus.APPLIED, limit=100)
            
            new_overrides = {}
            # Eskiden yeniye doğru (recent desc olduğu için ters çevirmeliyiz veya sonuncuyu almalıyız)
            # Burada en güncel olanı (ilk çıkanı) alıyoruz.
            for evo in reversed(applied):
                new_overrides[evo.policy_key] = evo.applied_value
            
            cls._cached_overrides = new_overrides
            logger.info(f"Policy overrides refreshed. {len(new_overrides)} policies active.")
        except Exception as e:
            logger.error(f"Failed to refresh policy overrides: {e}")

    @classmethod
    def get_policy_value(cls, key: str) -> Any:
        return cls._cached_overrides.get(key, cls.DEFAULT_POLICIES.get(key))

    # --- Specialized Getters ---
    
    @classmethod
    def get_veto_priority_order(cls) -> List[str]:
        return cls.get_policy_value("policy.veto.priority")

    @classmethod
    def is_archive_allowed_with_open_incident(cls) -> bool:
        return cls.get_policy_value("policy.archive.allowed_with_open_incident")

    @classmethod
    def get_replay_max_retries(cls) -> int:
        return cls.get_policy_value("policy.replay.max_retries")

    @classmethod
    def get_prime_risk_floor(cls) -> float:
        return cls.get_policy_value("policy.escalation.prime_risk_floor")

    @classmethod
    def is_policy_veto_enabled(cls) -> bool:
        return cls.get_policy_value("policy.conflict.policy_veto_enabled")
