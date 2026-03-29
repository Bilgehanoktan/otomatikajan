"""
CEO Router — Faz 8 Infra
Exposes CEO Engine findings and status.
"""

from fastapi import APIRouter, Depends
from auth.jwt_auth import get_current_user
from core.ceo_engine import get_ceo_engine

router = APIRouter(prefix="/ceo", tags=["CEO Engine"])

@router.get("/findings")
async def get_findings(current_user=Depends(get_current_user)):
    """CEO Engine tarafından bulunan iyileştirme fırsatlarını getir."""
    # CEOEngine findings listesi şu an transient, 
    # Gerçek uygulamada RepairOrchestrator incident'larına düşer.
    # Burada son bulguları mock olarak veya son Repair incidents olarak dönebiliriz.
    
    try:
        from repair.ingestion.incident_ingestor import incident_ingestor
        # CEO tarafından açılan açık incident'ları filtrele
        open_incidents = incident_ingestor.list_open()
        ceo_findings = [
            {
                "id": inc.incident_id,
                "timestamp": inc.created_at,
                "category": inc.module,
                "finding": inc.symptom,
                "severity": inc.severity.value,
                "status": "OPEN",
                "source": "CEO_ENGINE"
            }
            for inc in open_incidents if inc.source == "ceo_engine" or inc.module == "ceo_engine"
        ]
        
        # Faz 12.1 Enhancement: If no incidents, check suggested tasks directly from CEO Engine
        if not ceo_findings:
            from core.ceo_engine import get_ceo_engine
            # Return empty findings but include stats to indicate the engine is active
            return {"findings": [], "stats": {"open_opportunities": 0}}

        return {"findings": ceo_findings}
    except Exception as e:
        # In degraded mode, don't crash the UI but log the error
        return {"findings": [], "error": str(e)}

@router.post("/scan")
async def trigger_scan(current_user=Depends(get_current_user)):
    """CEO scan'ini manuel tetikle."""
    ceo = get_ceo_engine()
    results = await ceo.audit_codebase()
    return {"results": results}
