"""
Self-Improvement Observer (Consolidated from improvement_v1)
[CONSOLIDATION] Eski improvement_v1/observer.py'nin aktif versiyonu.
Sistemdeki iyileÅŸtirme fÄ±rsatlarÄ±nÄ± tarar.
"""
import uuid
from typing import List, Dict, Any
from packages.improvement_engine.models import ImprovementOpportunity
from packages.observability.logging import get_logger

logger = get_logger("improvement.observer")


class ImprovementObserver:
    """Sistemdeki iyileÅŸtirme fÄ±rsatlarÄ±nÄ± tespit eden gÃ¶zlemci."""

    async def scan(self) -> List[ImprovementOpportunity]:
        """
        Sistemi tarar ve iyileÅŸtirme fÄ±rsatlarÄ±nÄ± bulur.
        """
        logger.info("ImprovementObserver: Sistem taranÄ±yor...")
        opportunities = []

        try:
            opportunities.extend(await self._scan_agent_failures())
            opportunities.extend(await self._scan_endpoint_errors())
        except Exception as e:
            logger.error(f"Observer scan hatasÄ±: {e}")

        return opportunities

    async def scan_for_issues(self) -> List[Dict[str, Any]]:
        """
        Eski API uyumluluÄŸu â€” core/improvement/gate.py tarafÄ±ndan kullanÄ±lÄ±r.
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
        """Agent baÅŸarÄ± oranlarÄ±nÄ± tarar."""
        # GerÃ§ek DB taramasÄ± burada yapÄ±lÄ±r (stub)
        return []

    async def _scan_endpoint_errors(self) -> List[ImprovementOpportunity]:
        """API endpoint hata oranlarÄ±nÄ± tarar."""
        return []


# Singleton
observer = ImprovementObserver()

