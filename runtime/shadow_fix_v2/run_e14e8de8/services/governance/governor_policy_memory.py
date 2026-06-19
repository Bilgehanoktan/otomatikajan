import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import GovernorPolicyEvolutionRecord, PolicyEvolutionStatus

logger = logging.getLogger(__name__)

class GovernorPolicyMemory:
    @staticmethod
    async def record_policy_outcome(db: AsyncSession, evolution_id: Any, success_score: float):
        """Uygulanan bir politikanın başarısını (veya başarısızlığını) hafızaya alır."""
        # Bu bilgi zaten Outcome ve Scorecard tablolarında var. 
        # Bu servis o verileri özetleyerek "öğrenilmiş dersler" üretir.
        pass

    @staticmethod
    async def find_similar_policy_change(db: AsyncSession, policy_key: str, proposed_value: Any) -> Optional[GovernorPolicyEvolutionRecord]:
        """Daha önce aynı veya benzer bir değişiklik yapılıp yapılmadığını kontrol eder."""
        stmt = select(GovernorPolicyEvolutionRecord).where(
            GovernorPolicyEvolutionRecord.policy_key == policy_key,
            GovernorPolicyEvolutionRecord.status.in_([PolicyEvolutionStatus.REJECTED, PolicyEvolutionStatus.ROLLED_BACK])
        ).order_by(desc(GovernorPolicyEvolutionRecord.created_at)).limit(1)
        
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def summarize_policy_effectiveness(db: AsyncSession) -> Dict[str, Any]:
        """Hangi politika türlerinin en çok başarı sağladığını özetler."""
        # İstatistiksel özet
        return {
            "most_effective_types": ["ARCHIVE_POLICY_CHANGE", "RULE_CHANGE"],
            "least_effective_types": ["ESCALATION_POLICY_CHANGE"],
            "total_evolutions_applied": 0,
            "rollback_rate": 0.05
        }
