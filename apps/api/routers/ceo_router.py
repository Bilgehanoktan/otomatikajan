"""
CEO Router — Faz 8 Infra
Exposes CEO Engine findings and status.
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from apps.api.routers.auth.jwt_auth import get_current_user
from packages.orchestration.ceo.engine import get_ceo_engine
from packages.observability.logging import get_logger

logger = get_logger("api.ceo")
router = APIRouter(prefix="/ceo", tags=["CEO Engine"])

@router.get("/overview")
async def get_overview(current_user=Depends(get_current_user)):
    """CEO Dashboard'u için özet metrikleri ve manifestoyu getir."""
    ceo = get_ceo_engine()
    return await ceo.get_overview()

@router.get("/findings")
async def get_findings(current_user=Depends(get_current_user)):
    """CEO Engine tarafından bulunan iyileştirme fırsatlarını ve önerileri getir."""
    try:
        from packages.persistence.session import session_scope
        from packages.persistence.models import ImprovementOpportunity, CEOSuggestedTask
        from sqlalchemy import select
        
        async with session_scope() as db:
            # 1. Açık fırsatları getir
            res_ops = await packages.persistence.execute(
                select(ImprovementOpportunity)
                .where(ImprovementOpportunity.status == "open")
                .order_by(ImprovementOpportunity.priority_score.desc())
            )
            ops = res_ops.scalars().all()
            
            # 2. Önerilen görevleri getir
            res_sug = await packages.persistence.execute(
                select(CEOSuggestedTask)
                .where(CEOSuggestedTask.status == "suggested")
            )
            sugs = res_sug.scalars().all()

            # UI için uyumlu formata dönüştür
            findings = []
            for op in ops:
                findings.append({
                    "id": str(op.id),
                    "timestamp": op.created_at,
                    "category": op.category,
                    "finding": op.title,
                    "severity": op.severity,
                    "priority_score": op.priority_score,
                    "status": "OPEN",
                    "description": op.description,
                    "source": "CEO_ENGINE"
                })
            
            for sug in sugs:
                findings.append({
                    "id": str(sug.id),
                    "timestamp": sug.created_at,
                    "category": "suggestion",
                    "finding": sug.title,
                    "severity": sug.priority,
                    "priority_score": 0,
                    "status": "SUGGESTED",
                    "description": sug.description,
                    "source": "CEO_STRATEGY"
                })

            return {
                "findings": findings,
                "stats": {
                    "open_opportunities": len(ops),
                    "suggested_tasks": len(sugs)
                },
                "is_fallback": False,
                "source_of_truth": "sovereign_db"
            }
            
    except Exception as e:
        logger.error(f"CEO findings error: {e}")
        return {
            "findings": [],
            "error": str(e),
            "is_fallback": True,
            "source_of_truth": "unavailable"
        }

@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks, current_user=Depends(get_current_user)):
    """CEO scan'ini manuel olarak arka planda tetikle."""
    ceo = get_ceo_engine()
    background_tasks.add_task(ceo.run_scan)
    return {"message": "CEO Scan arka planda başlatıldı."}
