"""
Self-Improvement Observer (Consolidated from improvement_v1)
[CONSOLIDATION] Eski improvement_v1/observer.py'nin aktif versiyonu.
Sistemdeki iyileştirme fırsatlarını tarar.
"""
import uuid
from typing import List, Dict, Any
from packages.orchestration.experimental.models import ImprovementOpportunity
from observability.logging import get_logger

logger = get_logger("improvement.observer")


class ImprovementObserver:
    """Sistemdeki iyileştirme fırsatlarını tespit eden gözlemci."""

    async def scan(self) -> List[ImprovementOpportunity]:
        """
        Sistemi tarar ve iyileştirme fırsatlarını bulur.
        """
        logger.info("ImprovementObserver: Sistem taranıyor...")
        opportunities = []

        try:
            opportunities.extend(await self._scan_agent_failures())
            opportunities.extend(await self._scan_endpoint_errors())
        except Exception as e:
            logger.error(f"Observer scan hatası: {e}")

        return opportunities

    async def scan_for_issues(self) -> List[Dict[str, Any]]:
        """
        Eski API uyumluluğu — core/improvement/gate.py tarafından kullanılır.
        """
        opportunities = await self.scan()
        return [
            {
                "agent_id": opp.id,
                "reason": opp.description,
                "severity": opp.severity,
                "affected_files": opp.affected_files,
                "evidence": opp.evidence,
            }
            for opp in opportunities
        ]

    async def _scan_agent_failures(self) -> List[ImprovementOpportunity]:
        """Agent başarı oranlarını tarar."""
        # Gerçek DB taraması burada yapılır (stub)
        return []

    async def _scan_endpoint_errors(self) -> List[ImprovementOpportunity]:
        """API endpoint hata oranlarını tarar."""
        return []


# Singleton
observer = ImprovementObserver()
