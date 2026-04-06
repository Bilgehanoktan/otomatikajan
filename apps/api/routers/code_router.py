"""
Kod Üretim API Router — Faz 6
POST /api/v1/code/generate   -> Kod üretimi başlat
GET  /api/v1/code/results    -> Tüm üretimler
GET  /api/v1/code/{id}       -> Belirli üretim
GET  /api/v1/code/{id}/files -> Dosya listesi
GET  /api/v1/code/{id}/download -> ZIP indir
GET  /api/v1/code/{id}/files/{path} -> Tek dosya içeriği
GET  /api/v1/code/templates  -> Mevcut şablonlar
"""

import base64

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional

from apps.api.routers.auth.jwt_auth import get_current_user, get_optional_user
from packages.observability.logging import get_logger

router = APIRouter(prefix="/code", tags=["Code Generation"])
logger = get_logger("code_router")


# ── Lazy bağımlılıklar ────────────────────────────────────
def _orch():
    from packages.orchestration.context import orchestrator
    return orchestrator


# ── Request/Response Modelleri ────────────────────────────

class CodeGenerateRequest(BaseModel):
    title:       str   = Field(..., min_length=3, max_length=200)
    description: str   = Field(..., min_length=10, max_length=2000)
    template:    str   = Field("custom", description="fastapi_rest | react_spa | cli_tool | data_pipeline | fullstack | custom")
    run_review:  bool  = Field(True, description="Code review ajan çalışsın mı")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Blog API",
                "description": "Kullanıcıların post oluşturabildiği, yorum yapabildiği REST API",
                "template": "fastapi_rest",
                "run_review": True,
            }
        }


class CodeFileOut(BaseModel):
    path:        str
    language:    str
    lines:       int
    syntax_ok:   bool
    lint_count:  int
    agent_id:    str
    description: str = ""


class CodeResultOut(BaseModel):
    project_id:    str
    title:         str
    file_count:    int
    total_lines:   int
    languages:     list[str]
    quality_score: float
    created_at:    str
    review_summary:str = ""


# ── Endpoints ────────────────────────────────────────────

@router.get("/templates", summary="Kullanılabilir proje şablonları")
async def list_templates():
    """Desteklenen proje şablonlarını listele."""
    from sovereign_codegen import ProjectTemplate, TEMPLATE_SPECS
    return {
        t.value: {
            "name":        t.value,
            "description": TEMPLATE_SPECS.get(t, {}).get("description", t.value),
            "agents":      TEMPLATE_SPECS.get(t, {}).get("agents", []),
            "file_count":  len(TEMPLATE_SPECS.get(t, {}).get("files", [])),
        }
        for t in ProjectTemplate
    }


@router.post("/generate", summary="Kod üretimi başlat")
async def generate_code(
    req:  CodeGenerateRequest,
    user  = Depends(get_optional_user),
):
    """
    8 ajanı paralel kullanarak proje kodu üretir.
    Code review ajan otomatik çalışır ve lint kontrolleri uygulanır.
    Sonuç ZIP olarak indirilebilir.
    """
    from sovereign_codegen import get_code_engine, ProjectTemplate
    from packages.orchestration.domain.events import event_bus

    engine = get_code_engine()
    if not engine:
        raise HTTPException(503, "Kod motoru başlatılamadı")

    try:
        template = ProjectTemplate(req.template)
    except ValueError:
        template = ProjectTemplate.CUSTOM

    # Ajan registry'den al
    try:
        from packages.orchestration.agi.agent_registry import build_agents
        agents = build_agents()
    except Exception:
        agents = None

    user_email = user.email if user else "guest"
    logger.info(f"Kod üretimi başlatıldı: {req.title} [{template.value}] — {user_email}")

    try:
        result = await engine.generate(
            title=req.title,
            description=req.description,
            template=template,
            agents=agents,
            event_bus=event_bus if req.run_review else None,
        )
    except Exception as e:
        logger.error(f"Kod üretim hatası: {e}")
        raise HTTPException(500, f"Kod üretimi başarısız: {e}")

    return {
        "project_id":    result.project_id,
        "title":         result.title,
        "file_count":    len(result.files),
        "total_lines":   result.total_lines,
        "languages":     result.languages,
        "quality_score": result.quality_score,
        "created_at":    result.created_at,
        "files": [
            {
                "path":      f.path,
                "language":  f.language.value,
                "lines":     f.line_count(),
                "syntax_ok": f.syntax_ok,
                "lint_count":len(f.lint_issues),
                "agent_id":  f.agent_id,
            }
            for f in result.files
        ],
        "review_summary": result.review_summary[:500] if result.review_summary else "",
    }


@router.get("/results", summary="Tüm kod üretim sonuçları")
async def list_results(user = Depends(get_optional_user)):
    from sovereign_codegen import get_code_engine
    engine = get_code_engine()
    if not engine: return []
    return await engine.list_results()


@router.get("/{project_id}", summary="Belirli üretim detayı")
async def get_result(project_id: str, user = Depends(get_optional_user)):
    from sovereign_codegen import get_code_engine
    engine = get_code_engine()
    if not engine: raise HTTPException(503, "Motor başlatılamadı")
    result = await engine.get_result(project_id)
    if not result:
        raise HTTPException(404, "Üretim bulunamadı")

    return {
        "project_id":    result.project_id,
        "title":         result.title,
        "file_count":    len(result.files),
        "total_lines":   result.total_lines,
        "languages":     result.languages,
        "quality_score": result.quality_score,
        "created_at":    result.created_at,
        "review_summary":result.review_summary,
        "files": [
            {
                "path":        f.path,
                "language":    f.language.value,
                "lines":       f.line_count(),
                "syntax_ok":   f.syntax_ok,
                "lint_issues": f.lint_issues,
                "review_notes":f.review_notes,
                "agent_id":    f.agent_id,
            }
            for f in result.files
        ],
    }


@router.get("/{project_id}/file", summary="Tek dosya içeriği")
async def get_file_content(
    project_id: str,
    path: str = Query(..., description="Dosya yolu, örn: src/api.py"),
    user = Depends(get_optional_user),
):
    from sovereign_codegen import get_code_engine
    engine = get_code_engine()
    if not engine: raise HTTPException(503, "Motor başlatılamadı")
    result = await engine.get_result(project_id)
    if not result:
        raise HTTPException(404, "Üretim bulunamadı")

    cf = next((f for f in result.files if f.path == path), None)
    if not cf:
        raise HTTPException(404, f"Dosya bulunamadı: {path}")

    return {
        "path":        cf.path,
        "language":    cf.language.value,
        "content":     cf.content,
        "syntax_ok":   cf.syntax_ok,
        "lint_issues": cf.lint_issues,
        "review_notes":cf.review_notes,
        "lines":       cf.line_count(),
        "agent_id":    cf.agent_id,
    }


@router.get("/{project_id}/download", summary="ZIP olarak indir")
async def download_zip(
    project_id: str,
    user = Depends(get_optional_user),
):
    """Tüm üretilen dosyaları ZIP arşiv olarak döndür."""
    from sovereign_codegen import get_code_engine
    engine = get_code_engine()
    if not engine: raise HTTPException(503, "Motor başlatılamadı")
    result = await engine.get_result(project_id)
    if not result:
        raise HTTPException(404, "Üretim bulunamadı")

    zip_bytes = result.to_zip()
    safe_title = result.title.replace(" ", "_").replace("/", "-")[:50]

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}_{project_id}.zip"',
            "Content-Length": str(len(zip_bytes)),
        },
    )
