"""
Self-Improvement Observer (Consolidated from improvement_v1)
[CONSOLIDATION] Eski improvement_v1/observer.py'nin aktif versiyonu.
Sistemdeki iyileÅŸtirme fÄ±rsatlarÄ±nÄ± tarar.
"""
import uuid
from typing import List, Dict, Any
from sqlalchemy import select, func, and_
from packages.improvement_engine.models import ImprovementOpportunity
from packages.persistence.session import get_db
from packages.persistence.models.core_models import SubTask, ApiMetric, ProjectStatus, ImprovementOpportunity as DB_ImpOp
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
        """SubTask performansını tarar: Hatalar ve düşük kalite."""
        ops = []
        async with get_db() as db:
            try:
                # 1. Hatalı ve Düşük Kaliteli Görevleri Bul
                stmt = select(SubTask).where(
                    and_(
                        SubTask.completed_at != None,
                        (SubTask.status == ProjectStatus.ERROR) | (SubTask.quality_score < 0.6) | (SubTask.attempts > 1)
                    )
                ).limit(50)
                
                result = await db.execute(stmt)
                tasks = result.scalars().all()
                
                for task in tasks:
                    desc = f"Agent Failure/Suboptimal: {task.agent_id} on task {task.id}. "
                    if task.status == ProjectStatus.ERROR: desc += "Status: ERROR."
                    elif task.quality_score < 0.6: desc += f"Quality: {task.quality_score}."
                    
                    op = ImprovementOpportunity(
                        id=str(task.id),
                        source_metric="agent_failure",
                        severity="high" if task.status == ProjectStatus.ERROR else "medium",
                        description=desc,
                        affected_files=[], # Gelecekte logic_file tespiti eklenecek
                        evidence={
                            "attempts": task.attempts,
                            "error": str(task.result[:500]),
                            "agent_id": task.agent_id,
                            "quality_score": task.quality_score
                        }
                    )
                    ops.append(op)
            except Exception as e:
                logger.error(f"Agent failure scan failed: {e}")
        return ops

    async def _scan_endpoint_errors(self) -> List[ImprovementOpportunity]:
        """API Performansını tarar: 5xx Hataları ve Yavaşlık."""
        ops = []
        async with get_db() as db:
            try:
                stmt = select(ApiMetric).where(
                    (ApiMetric.status_code >= 500) | (ApiMetric.response_ms > 5000)
                ).limit(20)
                
                result = await db.execute(stmt)
                metrics = result.scalars().all()
                
                for m in metrics:
                    op = ImprovementOpportunity(
                        id=str(m.id),
                        source_metric="endpoint_error" if m.status_code >= 500 else "endpoint_latency",
                        severity="high" if m.status_code >= 500 else "medium",
                        description=f"Performance/Reliability issue at {m.method} {m.endpoint}",
                        affected_files=[],
                        evidence={
                            "status_code": m.status_code,
                            "latency_ms": m.response_ms,
                            "endpoint": m.endpoint,
                            "method": m.method
                        }
                    )
                    ops.append(op)
            except Exception as e:
                logger.error(f"Endpoint error scan failed: {e}")
        return ops


# Singleton
observer = ImprovementObserver()

