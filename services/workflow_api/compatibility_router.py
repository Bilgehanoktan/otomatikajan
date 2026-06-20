from typing import Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from services.auth.jwt_auth import require_permission
from services.workflow_api.governance_router import AuditBundleCreate

# Moved to local scope to prevent circular/hang issues
# from services.workflow_api.governance_router import AuditBundleCreate

router = APIRouter(tags=["Compatibility & Stubs"])

@router.get("/federation")
async def list_federation_stub(): return []

@router.get("/safety")
async def list_safety_stub(): return []

@router.get("/training")
async def list_training_stub(): return []

@router.get("/compliance/policies")
@router.get("/compliance/policies/")
async def list_compliance_policies_compat(response: Response):
    from services.workflow_api.governance_router import list_retention_policies
    return await list_retention_policies(response)

@router.get("/evolution/state")
@router.get("/evolution/state/")
async def get_evolution_state_compat():
    from services.workflow_api.governance_router import get_evolution_state
    return await get_evolution_state()

@router.get("/costs")
async def list_costs_stub(): return []

@router.get("/audit")
async def list_audit_stub(): return []

@router.get("/audit-bundles")
@router.get("/audit-bundles/")
@router.get("/compliance/audit-bundles")
@router.get("/compliance/audit-bundles/")
async def list_audit_bundles_compat(response: Response):
    from services.workflow_api.governance_router import list_audit_bundles
    return await list_audit_bundles(response)

@router.post("/audit-bundles")
@router.post("/audit-bundles/")
@router.post("/compliance/audit-bundles")
@router.post("/compliance/audit-bundles/")
async def create_audit_bundle_compat(
    req: AuditBundleCreate,
    identity: dict[str, Any] = Depends(require_permission("audit.create"))
):
    from services.workflow_api.governance_router import create_audit_bundle_endpoint

    return await create_audit_bundle_endpoint(req, identity)

@router.get("/mesh")
async def list_mesh_stub(): return []

@router.post("/ops/handover")
@router.post("/ops/handover/")
async def handover_compat(
    project_id: str,
    dry_run: bool = True,
    identity: dict[str, Any] = Depends(require_permission("ops.handover"))
):
    from services.workflow_api.governance_router import trigger_handover
    return await trigger_handover(project_id, dry_run, identity)

@router.get("/verifiers")
async def list_verifiers_stub(): return []

@router.get("/governance-lineage")
async def list_lineage_stub(): return []

@router.get("/policy-proposals")
async def list_policies_stub(): return []

@router.get("/self-tuning")
async def list_tuning_stub(): return []

@router.get("/projects")
async def list_projects_stub(): return []

@router.get("/analytics/costs/summary")
async def legacy_cost_summary_stub():
    return {
        "total_cost_usd": 0.0,
        "budget_limit_usd": 1000.0,
        "usage_pct": 0.0,
        "top_projects": [],
    }

class AnalyzeRequest(BaseModel):
    query: str
    user_id: str | None = None

@router.post("/orchestration/planner/analyze")
async def analyze_query(req: AnalyzeRequest):
    query = req.query.strip().lower()
    
    # 1. Check if user wants a CEO strategic scan
    if any(keyword in query for keyword in ["tara", "scan", "analiz", "suggestion", "bulgu"]):
        try:
            from services.orchestration.ceo.router import get_ceo_engine
            ceo = get_ceo_engine()
            findings = await ceo.run_scan()
            findings_count = len(findings) if findings else 0
            
            response = f"📊 **Stratejik Tarama Başlatıldı ve Tamamlandı.**\n" \
                       f"🔍 Bulunan yeni fırsat/bulgu sayısı: **{findings_count}**\n\n"
            
            if findings_count > 0:
                response += "**Son Bulgular:**\n"
                for idx, f in enumerate(findings[:5], 1):
                    title = getattr(f, "title", str(f))
                    response += f"{idx}. {title}\n"
            else:
                response += "✅ Kritik bir açık veya iyileştirme fırsatı saptanmadı."
                
            return {"response": response}
        except Exception as e:
            return {"response": f"❌ Stratejik tarama başarısız oldu: {str(e)}"}
            
    # 2. General LLM Assistant response
    try:
        from libs.llm.model_orchestrator import model_orchestrator
        system_prompt = (
            "Sen Sovereign AGI (Faz 12.1) sisteminin otonom stratejik asistanısın. "
            "Kullanıcıya sistem yönetimi, otonom denetleyici (BilgeAPI), hata giderme (self-repair) "
            "ve otonom ajanlar konularında yardımcı oluyorsun. Yanıtlarında Markdown formatı kullan, "
            "profesyonel ve Türkçe yanıt ver. Kısa ve öz ol."
        )
        llm_response = await model_orchestrator.generate(prompt=req.query, system_prompt=system_prompt)
        return {"response": llm_response}
    except Exception as e:
        return {"response": f"🔄 İstek alındı ancak AGI çekirdeği yanıt veremedi: {str(e)}"}
