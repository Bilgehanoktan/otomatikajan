"""
Repair Admin Router — Faz 11
Policy yönetimi, benchmark metrikleri, lessons store endpoint'leri.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from apps.api.routers.auth.jwt_auth import get_current_user, require_admin
from observability.logging import get_logger

router = APIRouter(prefix="/repair/admin", tags=["Self-Repair-Admin"])
_log  = get_logger("api.repair_admin")


# ── Request Models ─────────────────────────────────────────────

class PolicyUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    value:   Optional[object] = None

class PolicyAddRequest(BaseModel):
    name:        str
    description: str
    enabled:     bool  = True
    value:       Optional[object] = None

class FeedbackRequest(BaseModel):
    job_id:          str
    pr_id:           str
    decision:        str           # approved | rejected | merged
    feedback_code:   str
    feedback_note:   str  = ""
    module:          str  = ""
    incident_class:  str  = ""
    hypothesis_used: str  = ""


# ── Policy Endpoints ───────────────────────────────────────────

@router.get("/policies")
async def list_policies(current_user=Depends(get_current_user)):
    """Tüm politika kurallarını listele."""
    from core.policy_registry import get_policy_registry
    return {"policies": get_policy_registry().list_all()}


@router.get("/policies/{policy_name}")
async def get_policy(policy_name: str, current_user=Depends(get_current_user)):
    from core.policy_registry import get_policy_registry
    rule = get_policy_registry().get(policy_name)
    if not rule:
        raise HTTPException(404, f"Policy bulunamadı: {policy_name}")
    return rule.to_dict()


@router.put("/policies/{policy_name}")
async def update_policy(
    policy_name: str,
    body: PolicyUpdateRequest,
    current_user=Depends(require_admin),
):
    """Policy'yi güncelle (admin only)."""
    from core.policy_registry import get_policy_registry
    rule = get_policy_registry().update(
        policy_name,
        enabled=body.enabled,
        value=body.value,
        updated_by=current_user.username if hasattr(current_user, "username") else "admin",
    )
    if not rule:
        raise HTTPException(404, f"Policy bulunamadı: {policy_name}")
    _log.info(f"Policy güncellendi: {policy_name} by {getattr(current_user, 'username', 'admin')}")
    return {"updated": rule.to_dict()}


@router.post("/policies")
async def add_policy(body: PolicyAddRequest, current_user=Depends(require_admin)):
    """Yeni policy kural ekle (admin only)."""
    from core.policy_registry import get_policy_registry, PolicyRule
    rule = get_policy_registry().add(PolicyRule(
        name=body.name,
        description=body.description,
        enabled=body.enabled,
        value=body.value,
        updated_by=current_user.username if hasattr(current_user, "username") else "admin",
    ))
    return {"created": rule.to_dict()}


@router.get("/policies/export/json")
async def export_policies(current_user=Depends(require_admin)):
    """Policy kurallarını JSON olarak dışa aktar."""
    from core.policy_registry import get_policy_registry
    import json
    return {"json": get_policy_registry().export_json()}


# ── Metrics Endpoints ──────────────────────────────────────────

@router.get("/metrics/summary")
async def metrics_summary(
    last_days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
):
    """Repair benchmark özeti."""
    from repair.verification.metrics_collector import get_metrics_store
    return await get_metrics_store().summary(last_days=last_days)


@router.get("/metrics/trends")
async def metrics_trends(
    last_days:   int = Query(14, ge=3, le=90),
    bucket_days: int = Query(2, ge=1, le=7),
    current_user=Depends(get_current_user),
):
    """Trend verileri (bucket'lar halinde)."""
    from repair.verification.metrics_collector import get_metrics_store
    return {"trends": get_metrics_store().trends(last_days, bucket_days)}


@router.get("/metrics/modules")
async def metrics_top_modules(
    top_n: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user),
):
    """En çok incident alan modüller."""
    from repair.verification.metrics_collector import get_metrics_store
    return {"modules": await get_metrics_store().top_modules(top_n)}


# ── Lessons / Feedback Endpoints ───────────────────────────────

@router.post("/feedback")
async def record_feedback(body: FeedbackRequest, current_user=Depends(get_current_user)):
    """İnsan reviewer geri bildirimini kaydet."""
    from repair.memory.lessons_store import get_lessons_store, FEEDBACK_CODES
    if body.feedback_code not in FEEDBACK_CODES:
        raise HTTPException(422, f"Geçersiz feedback_code. Geçerliler: {FEEDBACK_CODES}")
    rec = get_lessons_store().record(
        job_id          = body.job_id,
        pr_id           = body.pr_id,
        decided_by      = current_user.username if hasattr(current_user, "username") else "unknown",
        decision        = body.decision,
        feedback_code   = body.feedback_code,
        feedback_note   = body.feedback_note,
        module          = body.module,
        incident_class  = body.incident_class,
        hypothesis_used = body.hypothesis_used,
    )
    return {"recorded": rec.to_dict()}


@router.get("/feedback/recent")
async def list_recent_feedback(
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from repair.memory.lessons_store import get_lessons_store
    return {"feedback": get_lessons_store().list_recent(limit)}


@router.get("/feedback/stats")
async def feedback_stats(current_user=Depends(get_current_user)):
    from repair.memory.lessons_store import get_lessons_store
    return get_lessons_store().stats()


@router.get("/feedback/module/{module_name:path}")
async def module_feedback(module_name: str, current_user=Depends(get_current_user)):
    from repair.memory.lessons_store import get_lessons_store
    return get_lessons_store().module_feedback_summary(module_name)


# ── Ranker Stats ───────────────────────────────────────────────



@router.get("/lessons")
async def list_lessons(limit: int = 20, current_user=Depends(get_current_user)):
    """RC1 Alias: /feedback/recent ile aynı — lessons store listesi."""
    from repair.memory.lessons_store import get_lessons_store
    return {"lessons": get_lessons_store().list_recent(limit)}

@router.get("/lessons/stats")
async def lessons_stats(current_user=Depends(get_current_user)):
    """Lessons store istatistikleri."""
    from repair.memory.lessons_store import get_lessons_store
    store = get_lessons_store()
    records = store.list_recent(1000)
    return {"total": len(records), "recent": records[:5]}

@router.get("/ranker/stats")
async def ranker_stats(current_user=Depends(get_current_user)):
    """Root cause ranker istatistikleri."""
    from repair.analysis.root_cause_ranker import get_root_cause_ranker
    return get_root_cause_ranker().stats()
