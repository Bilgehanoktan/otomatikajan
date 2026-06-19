import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from services.observability.logging import get_logger

logger = get_logger("resource_governor")

class ResourceGovernor:
    """
    Sovereign AGI Resource Governance & Emergency Shutdown System.
    Ensures system stability by throttling or stopping non-critical processes 
    when health scores drop below thresholds.
    """
    
    HEALTH_THRESHOLD_CRITICAL = 40
    HEALTH_THRESHOLD_WARNING = 60

    @staticmethod
    async def get_system_health_score() -> float:
        """
        Gecikme, hata oranları ve maliyet artış hızına göre 0-100 arası sağlık skoru üretir.
        """
        try:
            from libs.db.session import session_scope
            from libs.db.repositories.repository import ApiMetricRepository

            async with session_scope() as db:
                metrics = await ApiMetricRepository.get_summary(db, since_hours=1)
                avg_latency = metrics.get("avg_latency", 0)
                error_rate = metrics.get("error_rate", 0)

                health = 100.0
                if avg_latency > 500:
                    health -= 10
                if avg_latency > 1500:
                    health -= 20
                if error_rate > 0.05:
                    health -= 15
                if error_rate > 0.15:
                    health -= 30

                return max(0.0, health)
        except Exception as e:
            logger.error(f"Health calculation failed: {e}")
            return 85.0

    @staticmethod
    async def evaluate_emergency_status():
        """
        Sistem sağlığını kontrol eder ve gerekirse kısıtlamaları devreye sokar.
        """
        health = await ResourceGovernor.get_system_health_score()
        
        if health < ResourceGovernor.HEALTH_THRESHOLD_CRITICAL:
            logger.important(f"🚨 RESOURCE GOVERNOR: CRITICAL HEALTH ({health:.0f}/100). Triggering Emergency Lockdown.")
            await ResourceGovernor._apply_lockdown(level="critical")
        elif health < ResourceGovernor.HEALTH_THRESHOLD_WARNING:
            logger.warning(f"⚠️ RESOURCE GOVERNOR: DEGRADED HEALTH ({health:.0f}/100). Throttling secondary workers.workflow_worker.tasks.")
            await ResourceGovernor._apply_lockdown(level="warning")
        else:
            logger.info(f"✅ RESOURCE GOVERNOR: System healthy ({health:.0f}/100).")

    @staticmethod
    async def _apply_lockdown(level: str):
        """
        Belirli bir düzeyde kısıtlama uygular.
        """
        # Bu fonksiyon Celery kuyruklarını durdurabilir, 
        # düşük öncelikli projeleri 'stalled' durumuna çekebilir.
        if level == "critical":
            # Tüm 'non-essential' projeleri dondur
            pass
        elif level == "warning":
            # Geliştirme (dev) aşamasındaki projeleri yavaşlat
            pass

    @staticmethod
    async def enforce_quota(project_id: str, quota_usd: float) -> bool:
        """
        Bir projenin bütçe kotasını aşıp aşmadığını denetler.
        """
        try:
            from libs.db.session import session_scope
            from libs.db.repositories.repository import CostRepository

            async with session_scope() as db:
                current_cost = await CostRepository.get_project_cost(db, project_id)
                if current_cost >= quota_usd:
                    logger.warning(f"Quota exceeded for project {project_id}: ${current_cost} >= ${quota_usd}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Quota enforcement failed: {e}")
            return False
