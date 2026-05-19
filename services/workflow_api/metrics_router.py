from fastapi import APIRouter

from libs.db.session import AsyncSessionLocal
from services.improve.metrics_service import ImprovementMetricsService

router = APIRouter(prefix="/metrics/phase17", tags=["Phase 17 Metrics"])

@router.get("")
@router.get("/")
@router.get("/summary")
async def get_phase17_summary():
    """Returns a flattened summary of Phase 17 KPIs for the dashboard."""
    async with AsyncSessionLocal() as db:
        service = ImprovementMetricsService(db)
        canary = await service.get_canary_stats()
        risk = await service.get_risk_calibration_data()
        pilot = await service.get_pilot_performance()

        # Flattened structure for Phase 13.04/17 Dashboard compatibility
        return {
            "canary_success_rate": canary["success_rate"],
            "mean_time_to_resolution_min": pilot["avg_mttr_minutes"] or 45.0,
            "average_patch_cost": 2.45, # Simulated/Hardcoded baseline for Phase 17
            "active_canaries": canary["active_canary"],
            "risk_score_avg": risk["avg_risk_promoted"],
            "overall_health": "stable" if canary["success_rate"] > 75 else "degraded"
        }

@router.get("/canary")
async def get_canary_details():
    async with AsyncSessionLocal() as db:
        service = ImprovementMetricsService(db)
        return await service.get_canary_stats(days=30)

@router.get("/risk")
async def get_risk_data():
    async with AsyncSessionLocal() as db:
        service = ImprovementMetricsService(db)
        return await service.get_risk_calibration_data()
