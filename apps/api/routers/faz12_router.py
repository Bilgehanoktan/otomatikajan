import json
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from auth.jwt_auth import get_current_user, require_admin
from observability.logging import get_logger
from api.resilience import circuit_breaker

router = APIRouter(prefix="/faz12", tags=["Faz12-AI-Engine"])
_log   = get_logger("api.faz12")


# ══════════════════════════════════════════════════════════════
# Request Models
# ══════════════════════════════════════════════════════════════

class DebateRequest(BaseModel):
    topic:      str        = Field(..., min_length=10)
    agent_a:    str        = Field(default="backend_dev", description="backend_dev | security | devops | ...")
    agent_b:    str        = Field(default="security", description="architect | qa_engineer | data_eng | ...")
    moderator:  str        = Field(default="architect")
    context:    str        = Field(default="")
    max_rounds: int        = Field(default=3, ge=1, le=5)

class SandboxRequest(BaseModel):
    code:    str = Field(..., description="Çalıştırılacak Python kodu")
    timeout: int = Field(default=10, ge=1, le=30)

class VectorLessonSaveRequest(BaseModel):
    symptom:     str
    module:      str
    resolution:  str
    job_id:      str
    incident_id: str = ""
    tags:        list[str] = Field(default_factory=list)

class DebateOutcome(BaseModel):
    debate_id: str
    topic: str
    consensus: str
    agreement_reached: bool
    rounds_count: int
    duration_s: float
    rounds: list[dict]


# ══════════════════════════════════════════════════════════════
# Debate Engine Endpoints
# ══════════════════════════════════════════════════════════════

ACTIVE_DEBATES_KEY = "faz12:active_debates"


async def load_active_debates() -> list[dict[str, Any]]:
    from db.session import get_redis_client
    redis = get_redis_client()
    if redis is None:
        return []

    raw = await redis.get(ACTIVE_DEBATES_KEY)
    if not raw:
        return []

    try:
        return json.loads(raw)
    except Exception:
        return []


async def save_active_debates(items: list[dict[str, Any]]) -> None:
    from db.session import get_redis_client
    redis = get_redis_client()
    if redis is None:
        return

    await redis.set(ACTIVE_DEBATES_KEY, json.dumps(items))


@router.post("/debate/run", response_model=DebateOutcome)
@circuit_breaker(name="debate_engine", fail_threshold=3, recovery_timeout=60.0)
async def run_debate(body: DebateRequest, current_user=Depends(get_current_user)):
    """Multi-agent debate başlat. İki ajan kritik bir karar üzerinde tartışır."""
    try:
        from core.debate_engine import get_debate_engine
        from core.agi.cognitive.sovereign_cortex import sovereign_cortex as orch

        engine = get_debate_engine(model_orch=orch.model_orch, max_rounds=body.max_rounds)
        result = await engine.run_debate(
            topic=body.topic, agent_a=body.agent_a, agent_b=body.agent_b,
            moderator=body.moderator, context=body.context,
            max_rounds=body.max_rounds,
        )
        data = result.to_dict()

        active = await load_active_debates()
        active.append(data)
        if len(active) > 10:
            active.pop(0)
        await save_active_debates(active)

        return DebateOutcome(**data)
    except Exception as e:
        _log.error(f"Debate Engine hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Debate başlatılamadı: {str(e)}")


@router.get("/debate/active")
async def active_debates(current_user=Depends(get_current_user)):
    """Aktif veya son yapılan tartışmaları listele."""
    active = await load_active_debates()
    return {"active_debates": active}


@router.get("/debate/personas")
async def debate_personas(current_user=Depends(get_current_user)):
    """Tartışmaya katılabilecek ajan personallarını listele."""
    from core.agency.loader import agency_loader
    agents = agency_loader.list_agents()
    return {
        "personas": [
            {"id": a["id"], "name": a["name"], "emoji": a.get("emoji", "🤖")}
            for a in agents
        ]
    }


# ══════════════════════════════════════════════════════════════
# Sandbox Endpoints
# ══════════════════════════════════════════════════════════════

@router.post("/sandbox/run")
@circuit_breaker(name="sandbox_runner", fail_threshold=5, recovery_timeout=30.0)
async def run_sandbox(body: SandboxRequest, current_user=Depends(require_admin)):
    """Python kodunu güvenli sandbox'ta çalıştır (admin only)."""
    try:
        from core.sandbox_runner import get_sandbox_runner
        # SRE Hardening: Kaynak sınırlarını API seviyesinde zorunlu kıl
        runner = get_sandbox_runner(use_docker=True)
        # Timeout kısıtlaması (API seviyesinde max 30s)
        safe_timeout = min(body.timeout, 30)
        
        result = await runner.run_python(body.code, timeout=safe_timeout)
        return result.to_dict()
    except Exception as e:
        _log.error(f"Sandbox hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Sandbox yürütme hatası: {str(e)}")


@router.post("/sandbox/check-patch")
async def check_patch_sandbox(
    diff:    str = Query(..., description="Unified diff metni"),
    current_user=Depends(get_current_user),
):
    """Patch diff'ini sandbox syntax kontrolünden geçir."""
    from core.sandbox_runner import get_sandbox_runner
    runner = get_sandbox_runner(use_docker=False)
    lines  = diff.split("\n")
    added  = [l[1:] for l in lines if l.startswith("+") and not l.startswith("+++")]
    code   = "\n".join(added)
    if not code.strip():
        return {"success": True, "message": "Eklenen satır yok"}
    result = await runner.run_python(
        f"import ast\nast.parse({repr(code)})\nprint('OK')", timeout=5
    )
    return result.to_dict()


@router.post("/sandbox/ruff")
async def ruff_check_sandbox(
    code: str = Query(...),
    current_user=Depends(get_current_user),
):
    """Ruff linter kontrolü."""
    from core.sandbox_runner import get_sandbox_runner
    runner = get_sandbox_runner(use_docker=False)
    result = await runner.run_ruff_check(code)
    return result.to_dict()


# ══════════════════════════════════════════════════════════════
# Model Router Endpoints
# ══════════════════════════════════════════════════════════════

@router.get("/model-router/route")
async def get_routing_decision(
    prompt:     str   = Query(...),
    agent_role: str   = Query(default="general"),
    task_type:  Optional[str] = Query(default=None),
    current_user=Depends(get_current_user),
):
    """Bir prompt için model routing kararını önizle."""
    from llm.model_router import get_model_router
    decision = get_model_router().route(prompt, agent_role=agent_role, task_type=task_type)
    return decision.to_dict()


@router.get("/model-router/stats")
async def model_router_stats(current_user=Depends(get_current_user)):
    """Model router istatistikleri."""
    from llm.model_router import get_model_router
    return get_model_router().stats()


@router.get("/model-router/complexity-map")
async def complexity_map(current_user=Depends(get_current_user)):
    """Karmaşıklık -> model eşlemesini göster."""
    from llm.model_router import _MODEL_MAP, TaskComplexity
    result = {}
    for provider, mapping in _MODEL_MAP.items():
        result[provider] = {c.value: m for c, m in mapping.items()}
    return {"complexity_map": result}


# ══════════════════════════════════════════════════════════════
# Vector Lessons Endpoints
# ══════════════════════════════════════════════════════════════

@router.get("/vector-lessons/search")
async def search_vector_lessons(
    symptom: str = Query(...), 
    module:  str = Query(default=""),
    limit:   int = Query(default=3, ge=1, le=10),
    current_user=Depends(get_current_user)
):
    """Benzer geçmiş çözümleri semantic search ile bul."""
    from repair.memory.vector_lessons import get_vector_lessons
    store   = get_vector_lessons()
    results = store.find_similar(symptom, module=module, limit=limit)
    return {
        "query":   {"symptom": symptom, "module": module},
        "results": [
            {**r.lesson.to_dict(), "similarity_score": r.score, "match_type": r.match_type}
            for r in results
        ],
        "count":   len(results)
    }

@router.post("/vector-lessons/save")
async def save_vector_lesson(
    symptom: str, module: str, resolution: str, 
    job_id: str = "", incident_id: str = "",
    current_user=Depends(get_current_user)
):
    """Başarılı bir onarımı hafızaya kaydet."""
    from repair.memory.vector_lessons import get_vector_lessons
    lesson = get_vector_lessons().save_lesson(
        symptom=symptom, module=module, resolution=resolution,
        job_id=job_id, incident_id=incident_id
    )
    return {"status": "ok", "lesson_id": lesson.lesson_id}

@router.get("/vector-lessons/stats")
async def vector_lessons_stats(current_user=Depends(get_current_user)):
    """Vektör veritabanı istatistikleri."""
    from repair.memory.vector_lessons import get_vector_lessons
    return get_vector_lessons().stats()

@router.get("/vector-lessons/module/{module_name}")
async def lessons_by_module(module_name: str, current_user=Depends(get_current_user)):
    """Modül bazlı çözümleri listele."""
    from repair.memory.vector_lessons import get_vector_lessons
    lessons = get_vector_lessons().find_similar_by_module(module_name)
    return {"module": module_name, "lessons": [l.to_dict() for l in lessons]}
