import logging
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import (
    GovernorMetricAggregateRecord, 
    GovernorAlertSeverity, 
    GovernorAlertType,
    GovernorDomain
)
from libs.db.repositories.governor_observability_repository import GovernorAlertRepo
from services.governance.governor_alert_config import GovernorAlertConfig

logger = logging.getLogger(__name__)

class GovernorAlertEngine:
    @staticmethod
    async def evaluate_rules(db: AsyncSession):
        """Metrikleri kontrol eder ve gerekirse alert üretir."""
        logger.info("Evaluating governance alert rules...")
        
        # En son metrikleri çek
        res = await db.execute(
            select(GovernorMetricAggregateRecord)
            .order_by(desc(GovernorMetricAggregateRecord.created_at))
            .limit(20)
        )
        metrics = {m.metric_key: m for m in res.scalars().all()}
        
        # 1. Accuracy Check
        if "decision_accuracy" in metrics:
            m = metrics["decision_accuracy"]
            floor = GovernorAlertConfig.get_threshold("alerts.accuracy.min")
            if m.value < floor:
                await GovernorAlertRepo.create_alert(
                    db,
                    GovernorAlertType.DECISION_ACCURACY_DROP,
                    GovernorAlertSeverity.HIGH if m.value < 0.7 else GovernorAlertSeverity.WARNING,
                    "Decision Accuracy Drop",
                    f"Governance accuracy fell to {m.value*100}%, which is below threshold of {floor*100}%.",
                    domain=GovernorDomain.META,
                    metric_value=m.value,
                    threshold_value=floor
                )
        
        # Diğer kurallar...
