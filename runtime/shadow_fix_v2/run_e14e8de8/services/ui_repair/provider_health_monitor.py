import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from libs.db.models.ui_repair_models import UIProviderHealth, ProviderStatus

class ProviderHealthMonitor:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def record_metric(
        self, 
        provider: str, 
        latency_ms: int, 
        is_success: bool,
        cost_usd: float = 0.0
    ):
        result = await self.db_session.execute(
            select(UIProviderHealth).where(UIProviderHealth.provider == provider)
        )
        health = result.scalars().first()
        
        now = datetime.now(timezone.utc)
        
        if not health:
            health = UIProviderHealth(
                id=uuid.uuid4(),
                provider=provider,
                status=ProviderStatus.HEALTHY if is_success else ProviderStatus.DEGRADED,
                latency_ms=latency_ms,
                error_rate=0.0 if is_success else 1.0,
                last_success_at=now if is_success else None,
                last_failure_at=None if is_success else now,
                health_score=1.0 if is_success else 0.5,
                created_at=now
            )
            self.db_session.add(health)
        else:
            # Moving average calculation for error rate and health score
            alpha = 0.2
            new_error = 0.0 if is_success else 1.0
            health.error_rate = (1 - alpha) * health.error_rate + alpha * new_error
            health.latency_ms = int((1 - alpha) * health.latency_ms + alpha * latency_ms)
            
            if is_success:
                health.last_success_at = now
            else:
                health.last_failure_at = now
                
            # Determine status
            if health.error_rate > 0.5:
                health.status = ProviderStatus.UNAVAILABLE
                health.health_score = 0.0
            elif health.error_rate > 0.1:
                health.status = ProviderStatus.DEGRADED
                health.health_score = 0.6
            else:
                health.status = ProviderStatus.HEALTHY
                health.health_score = 1.0 - health.error_rate

        await self.db_session.commit()

    async def list_health_snapshots(self) -> List[UIProviderHealth]:
        result = await self.db_session.execute(select(UIProviderHealth))
        return list(result.scalars().all())
