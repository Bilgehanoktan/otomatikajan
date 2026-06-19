import abc
import asyncio
import time
from typing import Dict, List, Any, Optional
from uuid import UUID
from libs.db.models.governance_models import GovernorDomain
from services.governance.governor_slo_monitor import GovernorSloMonitor
from services.governance.governor_circuit_breaker import GovernorCircuitBreaker
from services.governance.governor_failover_policy import GovernorFailoverPolicy
from services.governance.governor_resilience_manager import GovernorResilienceManager
from sqlalchemy.ext.asyncio import AsyncSession

class BaseDomainGovernor(abc.ABC):
    """
    Tüm alan bazlı (Domain) Governor'lar için temel sınıf.
    """

    def __init__(self, domain: GovernorDomain):
        self.domain = domain

    @abc.abstractmethod
    async def build_case(self, project_id: UUID) -> Dict[str, Any]:
        """Proje durumunu analiz eder ve bağlam (context) oluşturur."""
        pass

    @abc.abstractmethod
    async def score_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Oluşturulan case için risk skoru üretir."""
        pass

    @abc.abstractmethod
    async def decide(self, scored_case: Dict[str, Any]) -> Dict[str, Any]:
        """Risk skoruna göre aksiyon önerisi üretir."""
        pass

    @abc.abstractmethod
    async def execute(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Kararı uygular (Sadece yetkisi varsa)."""
        pass

    @abc.abstractmethod
    async def emit_lineage(self, case: Dict[str, Any], decision: Dict[str, Any], outcome: Optional[Dict[str, Any]] = None):
        """Karar ve uygulama sürecini lineage servisine yazar."""
        pass

    def normalize_risk_score(self, score: float) -> int:
        """0.0 - 1.0 arası skoru 0-1000 arasına normalize eder."""
        return int(min(max(score, 0.0), 1.0) * 1000)

    def normalize_reason_codes(self, codes: List[str]) -> List[str]:
        """Reason code'ları standart formata getirir."""
        return [c.upper().replace(" ", "_") for c in codes]

    def mark_requires_prime(self, decision: Dict[str, Any]):
        """Kararı Prime incelemesi gerektirir olarak işaretler."""
        decision["requires_prime"] = 1
        decision["recommended_decision"] = "REQUIRES_PRIME_REVIEW"

    def mark_requires_quorum(self, decision: Dict[str, Any]):
        """Kararı Quorum onayı gerektirir olarak işaretler."""
        decision["requires_quorum"] = 1
        decision["recommended_decision"] = "REQUIRES_QUORUM"

    async def run_with_resilience(self, db: AsyncSession, project_id: UUID, timeout: float = 2.0) -> Dict[str, Any]:
        """
        Domain karar sürecini timeout, circuit breaker ve SLO ölçümü ile çalıştırır.
        """
        start_time = time.time()
        
        # 1. Circuit Breaker Kontrolü
        if await GovernorCircuitBreaker.is_open(db, self.domain):
            return GovernorFailoverPolicy.get_failover_decision(self.domain)
            
        try:
            # 2. Karar Süreci (Timeout ile)
            async with asyncio.timeout(timeout):
                case = await self.build_case(project_id)
                scored = await self.score_case(case)
                decision = await self.decide(scored)
                
                # Başarı kaydı
                latency = int((time.time() - start_time) * 1000)
                await GovernorSloMonitor.record_latency(db, self.domain, "decision", latency, success=True)
                await GovernorCircuitBreaker.record_success(db, self.domain)
                await GovernorResilienceManager.mark_healthy(db, self.domain)
                
                return decision
                
        except asyncio.TimeoutError:
            await GovernorResilienceManager.mark_failure(db, self.domain, "Timeout")
            await GovernorCircuitBreaker.record_failure(db, self.domain, "TIMEOUT")
            return GovernorFailoverPolicy.get_failover_decision(self.domain)
            
        except Exception as e:
            await GovernorResilienceManager.mark_failure(db, self.domain, str(e))
            await GovernorCircuitBreaker.record_failure(db, self.domain, type(e).__name__)
            return GovernorFailoverPolicy.get_failover_decision(self.domain)
