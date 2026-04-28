"""
Sovereign AGI — Phase 26
services/orchestration/trust_governor.py
Manages Federation Trust Scores, Decay Models, and Arbitration Learning (R-09).
"""
import logging
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import select, update
from libs.db.session import session_scope
from libs.db.models.core_models import FederationTrust, FederationTrustHistory, utcnow

_log = logging.getLogger("agi_trust_governor")

class TrustGovernor:
    """
    Federasyon Güven Yönetişimi.
    Kümülatif başarı, başarısızlık ve zaman bazlı azalma (decay) modellerini uygular.
    """

    DECAY_RATE = 0.05       # 1 birimlik inaktivite başına %5 düşüş (örnek basitleştirme)
    MAX_TRUST = 1.0
    MIN_TRUST = 0.1
    SUCCESS_BOOST = 0.02    # Her başarıda +0.02
    FAILURE_PENALTY = 0.10  # Her hatada -0.10
    ARBITRATION_WEIGHT = 0.05 # Başarılı tahkimde +0.05

    @classmethod
    async def record_outcome(cls, cluster_id: str, success: bool, is_arbitration: bool = False, impact: float = 1.0):
        """İş çıktısına göre güven puanını günceller ve geçmişe kaydeder."""
        async with session_scope() as db:
            # 1. Mevcut güven puanını al veya oluştur
            res = await db.execute(select(FederationTrust).where(FederationTrust.cluster_id == cluster_id))
            trust = res.scalar_one_or_none()
            
            if not trust:
                trust = FederationTrust(cluster_id=cluster_id, trust_score=0.8) # Yeni cluster 0.8 ile başlar
                db.add(trust)
                await db.flush()

            old_score = trust.trust_score
            delta = 0.0
            reason = "success" if success else "failure"

            # 2. Score Hesaplama
            if success:
                delta = cls.SUCCESS_BOOST * impact
                if is_arbitration:
                    delta += cls.ARBITRATION_WEIGHT
                    trust.arbitration_wins += 1
                    reason = "arbitration_win"
                trust.success_count += 1
            else:
                delta = -cls.FAILURE_PENALTY * impact
                trust.failure_count += 1
                reason = "failure"

            # 3. Apply and Clamp
            trust.trust_score = max(cls.MIN_TRUST, min(cls.MAX_TRUST, trust.trust_score + delta))
            trust.last_activity_at = utcnow()

            # 4. History Log
            db.add(FederationTrustHistory(
                cluster_id=cluster_id,
                trust_score=trust.trust_score,
                change_reason=reason,
                payload={
                    "old_score": round(old_score, 4),
                    "delta": round(delta, 4),
                    "impact": impact,
                    "metrics": {
                        "success": trust.success_count,
                        "failure": trust.failure_count,
                        "wins": trust.arbitration_wins
                    }
                }
            ))
            
            _log.info(f"[TRUST] Cluster {cluster_id}: {old_score:.2f} -> {trust.trust_score:.2f} (Reason: {reason})")
            # session_scope will auto-commit

    @classmethod
    async def apply_decay(cls, cluster_id: str):
        """Zamanla azalan güven modeli. İnaktif cluster'ların güveni yavaşça düşer."""
        async with session_scope() as db:
            res = await db.execute(select(FederationTrust).where(FederationTrust.cluster_id == cluster_id))
            trust = res.scalar_one_or_none()
            if not trust: return

            now = utcnow()
            # SQLite safe comparison: replace(tzinfo=None) if one is naive
            last_activity = trust.last_activity_at
            if last_activity.tzinfo is not None and now.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=None)
            elif last_activity.tzinfo is None and now.tzinfo is not None:
                now = now.replace(tzinfo=None)

            days_inactive = (now - last_activity).total_seconds() / 86400
            
            if days_inactive > 1.0: # 1 günden fazla inaktifse
                decay_factor = math.pow(1.0 - cls.DECAY_RATE, days_inactive)
                old_score = trust.trust_score
                trust.trust_score = max(cls.MIN_TRUST, trust.trust_score * decay_factor)
                
                db.add(FederationTrustHistory(
                    cluster_id=cluster_id,
                    trust_score=trust.trust_score,
                    change_reason="decay",
                    payload={"days_inactive": round(days_inactive, 2), "old_score": old_score}
                ))
                _log.info(f"[TRUST] Decay applied to {cluster_id}: {old_score:.2f} -> {trust.trust_score:.2f}")

    @classmethod
    async def record_agent_outcome(cls, agent_id: str, success: bool, impact: float = 1.0):
        """Ajan bazlı güven puanını ve performans metriklerini günceller."""
        from libs.db.models.core_models import AgentNode
        async with session_scope() as db:
            # 1. Ajanı bul (Registry name ile eşleştirme)
            res = await db.execute(select(AgentNode).where(AgentNode.name == agent_id))
            agent = res.scalar_one_or_none()
            
            if not agent:
                _log.warning(f"[TRUST] AgentNode {agent_id} bulunamadı, puan güncellenemedi.")
                return

            old_score = agent.trust_score
            delta = cls.SUCCESS_BOOST * impact if success else -cls.FAILURE_PENALTY * impact

            # 2. Metrikleri Güncelle
            if success:
                agent.success_count += 1
            else:
                agent.failure_count += 1

            # 3. Apply and Clamp
            agent.trust_score = max(cls.MIN_TRUST, min(cls.MAX_TRUST, agent.trust_score + delta))
            agent.last_heartbeat = utcnow()
            
            # 4. Autonomous Quarantine (Phase 12/13 Hardening)
            from libs.db.models.core_models import AgentStatus
            if agent.trust_score < 0.60 and agent.status != AgentStatus.QUARANTINED:
                agent.status = AgentStatus.QUARANTINED
                agent.capabilities["quarantine_reason"] = f"Trust score ({agent.trust_score:.2f}) dropped below safety threshold (0.60)"
                _log.warning(f"[TRUST-QUARANTINE] Agent {agent_id} ISOLATED due to low trust score.")

            _log.info(f"[TRUST-AGENT] {agent_id}: {old_score:.2f} -> {agent.trust_score:.2f} (Success: {success})")

# Singleton-like access
trust_governor = TrustGovernor()
