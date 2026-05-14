from typing import List, Dict, Any, Optional, cast
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from libs.db.models.ui_repair_models import UIRouteHealth, UIRouteHealthHist

class RouteHealthService:
    """
    Phase 6: Route Health Service.
    Manages persistent health state and historical snapshots.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_snapshot(self, route: str, status: str, http_status: int, response_time: float, run_id: Optional[UUID] = None):
        """
        Updates the health matrix and records a historical data point.
        """
        # 1. Update/Create UIRouteHealth
        stmt = select(UIRouteHealth).where(UIRouteHealth.route == route)
        health = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not health:
            health = UIRouteHealth(route=route)
            self.db.add(health)
            await self.db.flush()
            
        cast(Any, health).last_status = status
        cast(Any, health).last_http_status = http_status
        cast(Any, health).last_checked_at = datetime.now()
        if status == "PASS":
            cast(Any, health).last_success_at = cast(Any, health).last_checked_at
            cast(Any, health).failure_count = 0
        else:
            cast(Any, health).failure_count = (cast(Any, health).failure_count or 0) + 1
            
        cast(Any, health).avg_response_ms = (cast(Any, health).avg_response_ms * 0.8) + (response_time * 0.2) if cast(Any, health).avg_response_ms else response_time

        # 2. Record UIRouteHealthHist
        hist = UIRouteHealthHist(
            route_id=health.id,
            monitoring_run_id=run_id,
            route=route,
            status=status,
            http_status=http_status,
            response_time_ms=response_time
        )
        self.db.add(hist)
        
    async def get_route_history(self, route: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetches historical health data for a route."""
        stmt = select(UIRouteHealthHist).where(UIRouteHealthHist.route == route).order_by(desc(UIRouteHealthHist.captured_at)).limit(limit)
        res = await self.db.execute(stmt)
        points = res.scalars().all()
        return [{"status": p.status, "captured_at": p.captured_at} for p in points]
