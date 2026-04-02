"""
API Rotaları — Faz 2
• Proje oluşturma artık async (job queue) — anında job_id döner
• /projects/{id}/status ile durum takibi
• Rate limiting entegre
• Metrik entegre
"""

import os
import uuid
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from fastapi.concurrency import run_in_threadpool
from api.rate_limiter import rate_limit
from auth.jwt_auth import get_current_user
from api.mcp_router import router as mcp_router

router = APIRouter()
router.include_router(mcp_router)

# ── Yeni Sistem Altyapı Sağlığı ─────────────────────────
@router.get("/system/health", summary="Sistem Altyapı Sağlığı (Faz 12.1)")
async def system_health():
    import time
    from db.session import get_redis_client
    from config import REDIS_URL
    
    redis = get_redis_client()
    has_redis_config = bool(os.getenv("REDIS_URL") or REDIS_URL)
    
    tg_status = "UP" if not has_redis_config else "DOWN"
    # Eğer Redis konfigüre edilmişse heartbeat kontrolü yap
    if has_redis_config and redis is not None:
        try:
            hb = await redis.get("faz12:telegram_heartbeat")
            if hb and (int(time.time()) - int(hb)) <= 45: # Toleransı 45s'e çıkardık
                tg_status = "UP"
        except Exception:
            pass
    elif not has_redis_config:
        tg_status = "NOT_CONFIGURED"

    def check_celery():
        try:
            from config import QUEUE_BACKEND
            if (QUEUE_BACKEND or "auto").lower() == "inprocess":
                return "NOT_CONFIGURED"
                
            from tasks.celery_app import celery_app
            from config import REDIS_URL
            if REDIS_URL:
                celery_app.conf.broker_url = REDIS_URL
                celery_app.conf.result_backend = REDIS_URL
            
            # Synchronous call for threadpool
            i = celery_app.control.inspect(timeout=3.0)
            stats = i.ping()
            if stats and len(stats) > 0:
                return "UP"
            
            # Fallback
            active = i.active()
            if active is not None:
                return "UP"
                
            return "DOWN"
        except Exception:
            return "DOWN"

    celery_status = await run_in_threadpool(check_celery)

    # Calculate System Health Score (Faz 12.1 Logic)
    h_score = 1.0
    if tg_status != "UP" and celery_status == "UP": h_score = 0.6
    elif tg_status == "UP" and celery_status != "UP": h_score = 0.6
    elif tg_status != "UP" and celery_status != "UP": h_score = 0.1

    return {
        "status": "UP" if tg_status == "UP" and celery_status == "UP" else "DEGRADED",
        "health_score": h_score,
        "telegram_bot": {"status": tg_status},
        "celery_workers": {"status": celery_status}
    }

# ── Lazy bağımlılıklar ────────────────────────────────────
def _orch():
    from core.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
    return orchestrator

def _heal():
    from core.heal_engine import heal_engine
    return heal_engine

def _bus():
    from core.events import event_bus
    return event_bus

def _queue():
    from core.job_queue import job_queue
    return job_queue

def _metrics():
    from observability.metrics import metrics
    return metrics


# ── Pydantic ──────────────────────────────────────────────
class ProjectRequest(BaseModel):
    title:       str = Field(..., min_length=3, max_length=500)
    description: str = Field(default="", max_length=5000)
    async_mode:  bool = Field(default=True, description="True=kuyruk, False=blokla (test için)")



# Proje endpoint'leri task_write_router ve task_read_router'a taşındı.
# İş kuyruğu endpoint'leri monitoring_router'a taşındı.



# ════════════════════════════════════════════════════════
# AJAN & HEAL endpoint'leri
# ════════════════════════════════════════════════════════

@router.get("/agents/health", summary="Ajan sağlık durumu",
            dependencies=[Depends(rate_limit("heal_manual"))])
async def agent_health():
    orch = _orch(); heal = _heal()
    return {
        "system_score":  heal.system_health_score(),
        "agents":        orch.get_health(),
        "snapshots":     heal.agent_snapshots(),
        "backup_mode":   heal.agents_in_backup(),
        "recent_events": heal.recent_events(20),
        "system_report": heal.system_report(),
    }

@router.get("/heal/report", summary="Öz-iyileştirme raporu")
async def heal_report():
    return _heal().system_report()

@router.get("/heal/events", summary="İyileştirme olayları")
async def heal_events(n: int = 50):
    return _heal().recent_events(min(n, 200))

@router.get("/heal/agents/{agent_id}", summary="Ajan kurtarma geçmişi")
async def agent_recovery(agent_id: str):
    heal = _heal()
    return {
        "agent_id":         agent_id,
        "recovery_history": heal.recovery_history(agent_id),
        "snapshot":         next(
            (s for s in heal.agent_snapshots() if s["agent_id"] == agent_id), None
        ),
    }


# ════════════════════════════════════════════════════════
# LLM & MALİYET endpoint'leri
# ════════════════════════════════════════════════════════

@router.get("/llm/stats", summary="LLM sağlayıcı istatistikleri")
async def llm_stats():
    return _orch().model_orch.provider_stats()

@router.get("/cost/summary", summary="Maliyet özeti")
async def cost_summary():
    met = _metrics()
    snap = met.snapshot()
    try:
        from db.session import AsyncSessionLocal
        from db.repository import CostRepository
        async with AsyncSessionLocal() as db:
            total   = await CostRepository.total_cost(db)
            by_prov = await CostRepository.by_provider(db)
        return {"total_usd": total, "by_provider": by_prov, "metrics": snap["computed"]}
    except Exception:
        return {"metrics": snap["computed"]}


# ════════════════════════════════════════════════════════
# FAZ 3 — KALİTE & ONAY endpoint'leri
# ════════════════════════════════════════════════════════

def _gate():
    from quality.approval_gate import approval_gate
    return approval_gate

def _mem():
    from memory.retrieval import _fallback_store
    return _fallback_store


@router.get("/quality/summary", summary="Proje kalite özeti")
async def quality_summary():
    orch  = _orch()
    tasks = orch.list_tasks()
    scored = [t for t in tasks if t.avg_quality is not None]
    return {
        "total_projects": len(tasks),
        "scored_projects": len(scored),
        "avg_quality": round(sum(t.avg_quality for t in scored) / len(scored), 3) if scored else None,
        "by_project": [
            {"task_id": t.id, "title": t.title,
             "avg_quality": round(t.avg_quality, 3) if t.avg_quality else None,
             "status": str(t.status)}
            for t in tasks[-10:]
        ],
    }


@router.get("/quality/workflows", summary="Sistemde tanimli is akislari ve kalite profilleri")
async def get_workflows():
    try:
        from core.task_templates import TaskTemplate, QUALITY_PROFILES
        return {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "default_profile": t.default_profile,
                    "tags": t.tags
                } for t in TaskTemplate._registry.values()
            ],
            "profiles": QUALITY_PROFILES
        }
    except Exception as e:
        return {"error": str(e), "templates": [], "profiles": {}}

@router.get("/quality/agents", summary="Ajan bazlı kalite dağılımı")
async def quality_by_agent():
    orch   = _orch()
    tasks  = orch.list_tasks()
    agent_scores: dict[str, list[float]] = {}

    for task in tasks:
        for st in task.subtasks:
            if st.quality_score is not None:
                agent_scores.setdefault(st.agent_id, []).append(st.quality_score)

    return {
        agent: {
            "avg":     round(sum(scores) / len(scores), 3),
            "min":     round(min(scores), 3),
            "max":     round(max(scores), 3),
            "count":   len(scores),
            "reviewed":sum(1 for t in tasks for s in t.subtasks
                          if s.agent_id == agent and s.reviewed),
        }
        for agent, scores in agent_scores.items()
    }


# ── Onay Kapısı ───────────────────────────────────────────
@router.get("/approvals/pending", summary="Bekleyen onay talepleri")
async def pending_approvals():
    gate = _gate()
    return [
        {
            "id":          r.id,
            "operation":   r.operation,
            "description": r.description,
            "risk_level":  r.risk_level,
            "requested_by":r.requested_by,
            "created_at":  r.created_at,
            "timeout_s":   r.timeout_s,
        }
        for r in gate.pending_requests()
    ]


@router.post("/approvals/{request_id}/decide", summary="Onay ver veya reddet")
async def decide_approval(request_id: str, body: dict):
    gate   = _gate()
    approve = bool(body.get("approve", False))
    reason  = str(body.get("reason", ""))
    decided_by = str(body.get("decided_by", "admin"))
    req = gate.decide(request_id, approve, decided_by=decided_by, reason=reason)
    if not req:
        raise HTTPException(status_code=404, detail="Onay talebi bulunamadı")
    bus = _bus()
    await bus.emit(
        "approval.decided",
        request_id=request_id,
        approve=approve,
        severity="resolved" if approve else "warning",
        agent_id=decided_by,
        phase="approval",
        message=f"Onay {'verildi' if approve else 'reddedildi'}: {req.operation}",
    )
    return {"id": req.id, "status": req.status, "decided_by": req.decided_by}


@router.get("/approvals/history", summary="Onay geçmişi")
async def approval_history(n: int = 50):
    gate = _gate()
    return {
        "stats":   gate.stats(),
        "history": [
            {"id": r.id, "operation": r.operation, "risk_level": r.risk_level,
             "status": r.status, "decided_by": r.decided_by, "created_at": r.created_at}
            for r in gate.history(n)
        ],
    }


# ── Bellek endpoint'leri ──────────────────────────────────
@router.get("/memory/stats", summary="Bellek deposu istatistikleri")
async def memory_stats():
    store = _mem()
    db_stats = None
    try:
        from db.session import AsyncSessionLocal
        from sqlalchemy import select, func
        from db.models import Memory
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(func.count(Memory.id)))
            db_stats = {"db_total": result.scalar() or 0}
    except Exception:
        pass
    stats = store.stats()
    if db_stats:
        stats.update(db_stats)
    return stats


@router.post("/memory/search", summary="Bellek araması")
async def memory_search(body: dict):
    query      = str(body.get("query", ""))
    agent_id   = body.get("agent_id")
    top_k      = int(body.get("top_k", 8))
    if not query:
        raise HTTPException(status_code=422, detail="query gerekli")
    store = _mem()
    return store.search(query=query, agent_id=agent_id, top_k=top_k)


@router.delete("/memory/clear", summary="Bellek sıfırla (dev)",
               dependencies=[Depends(rate_limit("memory_clear"))])
async def clear_memory(current_user=Depends(get_current_user)):
    from memory.retrieval import _fallback_store
    _fallback_store._entries.clear()
    return {"cleared": True}
