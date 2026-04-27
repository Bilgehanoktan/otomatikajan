import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.governance_models import (
    GovernorOutcomeRecord, 
    GovernorDecisionQuality, 
    GovernorOutcomeType,
    PolicyEvolutionType,
    PolicyEvidenceType
)
from libs.db.repositories.governor_policy_repository import GovernorPolicyEvolutionRepo
from services.governance.governor_policy_config import GovernorPolicyConfig

logger = logging.getLogger(__name__)

class GovernorPolicyEvolutionEngine:
    @staticmethod
    async def scan_for_policy_candidates(db: AsyncSession, window_days: int = 14) -> List[Dict[str, Any]]:
        """Geçmiş verileri tarar ve politika iyileştirme adaylarını belirler."""
        logger.info(f"Scanning for policy evolution candidates (window: {window_days} days)...")
        
        proposals = []
        
        # 1. Analiz: Yüksek False Positive Kümesi (Örn: Archive işlemleri çok reddediliyorsa)
        fp_proposals = await GovernorPolicyEvolutionEngine._analyze_false_positives(db, window_days)
        proposals.extend(fp_proposals)
        
        # 2. Analiz: Operatörle Uyuşmazlık (Örn: Replay'ler manuel override ediliyorsa)
        disagreement_proposals = await GovernorPolicyEvolutionEngine._analyze_operator_disagreements(db, window_days)
        proposals.extend(disagreement_proposals)
        
        # 3. Analiz: Replay Başarı Oranı
        replay_proposals = await GovernorPolicyEvolutionEngine._analyze_replay_success(db, window_days)
        proposals.extend(replay_proposals)

        return proposals

    @staticmethod
    async def _analyze_false_positives(db: AsyncSession, window_days: int) -> List[Dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=window_days)
        
        # Örnek kural: Eğer "archive" kararları %30'dan fazla FALSE_POSITIVE çıkıyorsa 
        # ve açık incident varsa buna izin verme kuralını sıkılaştır.
        stmt = select(func.count(GovernorOutcomeRecord.id)).where(
            GovernorOutcomeRecord.created_at >= since,
            GovernorOutcomeRecord.decision.ilike("%archive%"),
            GovernorOutcomeRecord.quality == GovernorDecisionQuality.FALSE_POSITIVE
        )
        res = await db.execute(stmt)
        fp_count = res.scalar() or 0
        
        if fp_count > 5: # Basit eşik
            return [{
                "policy_key": "policy.archive.allowed_with_open_incident",
                "evolution_type": PolicyEvolutionType.ARCHIVE_POLICY_CHANGE,
                "proposed_value": False,
                "change_reason": f"Detected {fp_count} false positives in archive decisions while incidents were open.",
                "evidence_summary": {"type": PolicyEvidenceType.FALSE_POSITIVE_CLUSTER, "count": fp_count},
                "confidence_score": 0.85
            }]
        return []

    @staticmethod
    async def _analyze_operator_disagreements(db: AsyncSession, window_days: int) -> List[Dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=window_days)
        
        stmt = select(func.count(GovernorOutcomeRecord.id)).where(
            GovernorOutcomeRecord.created_at >= since,
            GovernorOutcomeRecord.operator_overrode == 1
        )
        res = await db.execute(stmt)
        override_count = res.scalar() or 0
        
        if override_count > 10:
            return [{
                "policy_key": "policy.escalation.prime_risk_floor",
                "evolution_type": PolicyEvolutionType.ESCALATION_POLICY_CHANGE,
                "proposed_value": max(0.1, GovernorPolicyConfig.get_prime_risk_floor() - 0.1),
                "change_reason": f"High operator override rate ({override_count} events). Lowering escalation floor to capture more edge cases.",
                "evidence_summary": {"type": PolicyEvidenceType.OPERATOR_DISAGREEMENT, "count": override_count},
                "confidence_score": 0.75
            }]
        return []

    @staticmethod
    async def _analyze_replay_success(db: AsyncSession, window_days: int) -> List[Dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=window_days)
        
        # Replay'ler sürekli başarısız oluyorsa max_retries'ı azaltmayı öner
        stmt = select(func.count(GovernorOutcomeRecord.id)).where(
            GovernorOutcomeRecord.created_at >= since,
            GovernorOutcomeRecord.decision.ilike("%replay%"),
            GovernorOutcomeRecord.final_outcome == GovernorOutcomeType.FAILED
        )
        res = await db.execute(stmt)
        fail_count = res.scalar() or 0
        
        if fail_count > 8:
            return [{
                "policy_key": "policy.replay.max_retries",
                "evolution_type": PolicyEvolutionType.REPLAY_POLICY_CHANGE,
                "proposed_value": 2,
                "change_reason": f"Frequent replay failures ({fail_count} events). Reducing max retries to prevent cycle waste.",
                "evidence_summary": {"type": PolicyEvidenceType.LOW_REPLAY_SUCCESS, "count": fail_count},
                "confidence_score": 0.70
            }]
        return []

    @classmethod
    async def run_suggestion_cycle(cls, db: AsyncSession) -> int:
        """Tarama yapar ve bulduğu adayları PROPOSED olarak kaydeder."""
        candidates = await cls.scan_for_policy_candidates(db)
        count = 0
        for c in candidates:
            # Mevcut aktif değeri al
            old_val = GovernorPolicyConfig.get_policy_value(c["policy_key"])
            
            # Eğer zaten aynı şey öneriliyorsa veya aktifse atla (opsiyonel)
            if old_val == c["proposed_value"]:
                continue
                
            await GovernorPolicyEvolutionRepo.create_evolution_proposal(
                db,
                policy_key=c["policy_key"],
                evolution_type=c["evolution_type"],
                proposed_value=c["proposed_value"],
                old_value=old_val,
                change_reason=c["change_reason"],
                evidence_summary=c["evidence_summary"],
                confidence_score=c["confidence_score"]
            )
            count += 1
        
        return count
