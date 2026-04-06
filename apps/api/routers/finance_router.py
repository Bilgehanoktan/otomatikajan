"""
Finance Router — Rota 2
• GET /finance/status   — Mevcut harcama ve bütçe durumu
• GET /finance/history  — Günlük maliyet serisi
• GET /finance/top-tasks — En maliyetli görevler
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from apps.api.routers.apps.api.routers.auth.jwt_auth import get_current_user
from packages.packages.observability.logging import get_logger
from config import BUDGET_USD

logger = get_logger("api.finance")
router = APIRouter(prefix="/finance", tags=["Finance"])

@router.get("/status", summary="Finansal durum ve bütçe analizi")
async def get_finance_status(current_user=Depends(get_current_user)):
    try:
        from packages.packages.observability.metrics import metrics
        from packages.llm_gateway.cost_calc import budget_check, format_cost
        
        snap = metrics.snapshot()
        spent = snap["computed"].get("total_cost_usd", 0.0)
        
        status = budget_check(spent, BUDGET_USD)
        
        return {
            "spent": spent,
            "spent_formatted": format_cost(spent),
            "budget": BUDGET_USD,
            "budget_formatted": format_cost(BUDGET_USD),
            "remaining": status["remaining"],
            "remaining_formatted": format_cost(status["remaining"]),
            "pct_used": status["pct_used"],
            "over_budget": status["over_budget"],
            "threshold_warning": status["pct_used"] > 80,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Finance status error: {e}")
        return {"error": str(e)}

@router.get("/history", summary="Günlük maliyet geçmişi")
async def get_finance_history(days: int = Query(7, ge=1, le=30), current_user=Depends(get_current_user)):
    try:
        from packages.persistence.session import AsyncSessionLocal
        from sqlalchemy import text
        
        # Bu kısım normalde LLMCostLog tablosundan gruplanarak çekilir.
        # Şimdilik DB'de veri yoksa boş liste döner.
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT 
                    DATE(created_at) as date,
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as call_count
                FROM llm_cost_logs
                WHERE created_at > NOW() - (INTERVAL '1 day' * :days)
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) ASC
            """)
            result = await packages.persistence.execute(query, {"days": days})
            history = [
                {"date": str(row.date), "cost": float(row.total_cost), "calls": row.call_count}
                for row in result
            ]
            
        return history
    except Exception as e:
        logger.warning(f"Finance history error (DB might be empty): {e}")
        return []

@router.get("/top-tasks", summary="En maliyetli projeler")
async def get_top_costly_tasks(limit: int = 5, current_user=Depends(get_current_user)):
    try:
        from packages.persistence.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT 
                    p.id, p.title, SUM(l.cost_usd) as total_cost
                FROM projects p
                JOIN llm_cost_logs l ON p.id = l.project_id
                GROUP BY p.id, p.title
                ORDER BY total_cost DESC
                LIMIT :limit
            """)
            result = await packages.persistence.execute(query, {"limit": limit})
            return [
                {"id": str(row.id), "title": row.title, "cost": float(row.total_cost)}
                for row in result
            ]
    except Exception as e:
        return []
