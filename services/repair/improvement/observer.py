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
                "evidence": getattr(opp, "evidence_detail", ""),
            }
            for opp in opportunities
        ]


    async def _scan_agent_failures(self) -> List[ImprovementOpportunity]:
        """
        Agent baÅŸarÄ± oranlarÄ±nÄ± ve hata desenlerini tarar.
        """
        from libs.db.session import AsyncSessionLocal
        from libs.db.models.core_models import WorkflowEvent, ImprovementOpportunity
        from sqlalchemy import select, func
        from datetime import datetime, timedelta, timezone

        opportunities = []
        logger.info("Agent hatalarÄ± taranÄ±yor...")

        try:
            async with AsyncSessionLocal() as session:
                # Son 24 saatteki hatalarÄ± grupla
                yesterday = datetime.now(timezone.utc) - timedelta(days=1)

                # Hata mesajlarına göre gruplama yaparak "pattern" yakala
                # Faz 12.1: Hatalı dosyaları da çekmek için SubTask ile join yapıyoruz
                from libs.db.models.core_models import SubTask
                from sqlalchemy import cast, String, case

                # Dialect-aware JSON extraction
                from libs.db.session import is_db_degraded
                is_postgres = not is_db_degraded()
                
                if is_postgres:
                    target_file_col = SubTask.input_data["target_file"].as_string()
                    # Postgres'te UUID karşılaştırması daha direkt yapılabilir
                    id_comparison = cast(SubTask.id, String) == WorkflowEvent.step_id
                else:
                    target_file_col = func.json_extract(SubTask.input_data, "$.target_file")
                    id_comparison = func.replace(cast(SubTask.id, String), "-", "") == func.replace(WorkflowEvent.step_id, "-", "")

                stmt = (
                    select(
                        func.min(WorkflowEvent.step_id).label("sample_step_id"),
                        WorkflowEvent.payload["error"].as_string().label("error_msg"),
                        func.count().label("err_count"),
                        target_file_col.label("target_file")
                    )
                    .join(
                        SubTask,
                        id_comparison,
                        isouter=True
                    )
                    .where(WorkflowEvent.event_type == "step_failed")
                    .where(WorkflowEvent.created_at >= yesterday)
                    .group_by("error_msg", "target_file")
                    .having(func.count() >= 2)
                )

                res = await session.execute(stmt)
                for row in res.all():
                    step_id, error_msg, count, target_file = row

                    # Bu pattern daha önce kaydedilmiş mi?
                    pattern_hash = ImprovementOpportunity.generate_hash("agent_failure", f"{step_id}:{error_msg}")

                    # JSON'dan tırnaklarla gelebilir (SQLite/PG), temizle
                    clean_file = target_file.strip('"') if target_file else None
                    affected_files = [clean_file] if clean_file and clean_file != "null" else []

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
                        affected_files=affected_files,
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

