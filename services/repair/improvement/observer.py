"""
Self-Improvement Observer (Consolidated from improvement_v1)
[CONSOLIDATION] Eski improvement_v1/observer.py'nin aktif versiyonu.
Sistemdeki iyileÅŸtirme fÄ±rsatlarÄ±nÄ± tarar.
"""
import uuid
from typing import List, Dict, Any
from libs.db.models.core_models import ImprovementOpportunity
from services.observability.logging import get_logger

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
        """
        Agent baÅŸarÄ± oranlarÄ±nÄ± ve hata desenlerini tarar.
        """
        from libs.db.session import AsyncSessionLocal as SessionLocal
        from libs.db.models.core_models import WorkflowEvent, ImprovementOpportunity
        from sqlalchemy import select, func
        from datetime import datetime, timedelta, timezone

        opportunities = []
        logger.info("Agent hatalarÄ± taranÄ±yor...")

        try:
            async with SessionLocal() as session:
                # Son 24 saatteki hatalarÄ± grupla
                yesterday = datetime.now(timezone.utc) - timedelta(days=1)
                
                # Hata mesajlarÄ±na gÃ¶re gruplama yaparak "pattern" yakala
                # Not: Payload iÃ§indeki hatayÄ± parse etmek iÃ§in basit bir model
                stmt = (
                    select(
                        WorkflowEvent.step_id,
                        WorkflowEvent.payload["error"].as_string().label("error_msg"),
                        func.count().label("err_count")
                    )
                    .where(WorkflowEvent.event_type == "step_failed")
                    .where(WorkflowEvent.created_at >= yesterday)
                    .group_by("error_msg", WorkflowEvent.step_id)
                    .having(func.count() >= 2) # En az 2 kez tekrarlananlarÄ± al
                )
                
                res = await session.execute(stmt)
                for row in res.all():
                    step_id, error_msg, count = row
                    
                    # Bu pattern daha Ã¶nce kaydedilmiÅŸ mi? (hash kontrolÃ¼)
                    pattern_hash = ImprovementOpportunity.generate_hash("agent_failure", f"{step_id}:{error_msg}")
                    
                    # Existing check (basitleÅŸtirilmiÅŸ)
                    opp = ImprovementOpportunity(
                        id=uuid.uuid4(),
                        source_type="agent_failure",
                        source_ref=step_id,
                        title=f"Recurring Failure in {step_id}",
                        description=f"Detected {count} failures with error: {error_msg}",
                        severity="high" if count > 5 else "medium",
                        category="reliability",
                        evidence_detail=error_msg,
                        pattern_hash=pattern_hash,
                        status="open"
                    )
                    opportunities.append(opp)
                    
        except Exception as e:
            logger.error(f"Agent failure scanning failed: {e}")

        return opportunities

    async def _scan_endpoint_errors(self) -> List[ImprovementOpportunity]:
        """API endpoint hata oranlarÄ±nÄ± tarar."""
        return []


# Singleton
observer = ImprovementObserver()

