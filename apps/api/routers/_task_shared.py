"""
Görev Yönetimi — Paylaşılan Bağımlılıklar (task_router paketinin ortak modülü)
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field

from apps.api.routers.apps.api.routers.auth.jwt_auth import get_current_user
from packages.packages.observability.logging import get_logger

logger = get_logger("api.tasks")


# ── DB bağımlılık ──────────────────────────────────────────
async def _db_session():
    from packages.persistence.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        yield db

class TaskCreateRequest(BaseModel):
    title:          str  = Field(..., min_length=3, max_length=500)
    description:    str  = Field(default="", max_length=10000)
    priority:       str  = Field(default="medium",
                                 pattern="^(critical|high|medium|low)$")
    source:         str  = Field(default="manual",
                                 pattern="^(manual|api|telegram|scheduled|research)$")
    assigned_agent: str  = Field(default="")
    tags:           list[str] = Field(default_factory=list)
    deadline:       Optional[datetime] = None
    notes:          str  = Field(default="")
    context:        str  = Field(default="", description="LLM için ek bağlam / prompt")
    budget_limit:   float = Field(default=0.0, description="Dolar cinsinden bütçe limiti (0 = limitsiz)")
    workflow_template: str = Field(default="default", description="Kullanılacak şablon (plan, hotfix vb.)")
    quality_profile: str   = Field(default="standard", description="standard, strict, veya production")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Onay kriterleri listesi")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Kullanıcı yetkilendirme servisi",
                "description": "JWT tabanlı auth sistemi kur",
                "priority": "high",
                "source": "manual",
                "tags": ["auth", "backend"],
            }
        }


class TaskUpdateRequest(BaseModel):
    title:          Optional[str]  = Field(None, min_length=3, max_length=500)
    description:    Optional[str]  = Field(None, max_length=10000)
    priority:       Optional[str]  = Field(None, pattern="^(critical|high|medium|low)$")
    assigned_agent: Optional[str]  = None
    tags:           Optional[list[str]] = None
    deadline:       Optional[datetime] = None
    notes:          Optional[str]  = None
    workflow_template: Optional[str] = None
    quality_profile: Optional[str] = None
    acceptance_criteria: Optional[list[str]] = None



# ── Yardımcı: project -> dict ───────────────────────────────
def _project_to_dict(p, subtasks=None, logs=None, agi_metadata=None) -> dict:
    result = {
        "id":            str(p.id),
        "title":         p.title,
        "description":   p.description,
        "status":        p.status,
        "source":        p.source,
        "priority":      p.priority,
        "progress_pct":  p.progress_pct,
        "tags":          p.tags or [],
        "assigned_agent":p.assigned_agent,
        "job_id":        p.job_id or "",
        "notes":         p.notes or "",
        "error_detail":  p.error_detail or "",
        "retry_count":   p.retry_count,
        "total_cost":    p.total_cost,
        "budget_limit":  p.budget_limit,
        "created_at":    p.created_at.isoformat() if p.created_at else None,
        "started_at":    p.started_at.isoformat() if p.started_at else None,
        "completed_at":  p.completed_at.isoformat() if p.completed_at else None,
        "deadline":      p.deadline.isoformat() if p.deadline else None,
        "cancelled_at":  p.cancelled_at.isoformat() if p.cancelled_at else None,
        "cancelled_by":  p.cancelled_by or "",
        "report":        p.report or "",
        "workflow_template": getattr(p, "workflow_template", "default"),
        "quality_profile":   getattr(p, "quality_profile", "standard"),
        "acceptance_criteria": getattr(p, "acceptance_criteria", []),
        "review_required":   getattr(p, "review_required", False),
        "execution_context": getattr(p, "execution_context", {}),
        "agi_metadata": agi_metadata
    }
    if subtasks is not None:
        result["subtasks"] = [
            {
                "id":          str(s.id),
                "agent_id":    s.agent_id,
                "status":      s.status,
                "attempts":    s.attempts,
                "recovered":   s.recovered,
                "llm_provider":s.llm_provider,
                "input_tokens":s.input_tokens,
                "output_tokens":s.output_tokens,
                "cost_usd":    s.cost_usd,
                "latency_s":   s.latency_s,
                "quality_score": getattr(s, "quality_score", 0.0),
                "reviewed":    getattr(s, "reviewed", False),
                "review_notes": getattr(s, "review_notes", []),
                "result_preview": (s.result[:500] + "…") if s.result and len(s.result) > 500 else (s.result or ""),
                "created_at":  s.created_at.isoformat() if s.created_at else None,
                "completed_at":s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in subtasks
        ]
    if logs is not None:
        result["logs"] = [
            {
                "id":       str(l.id),
                "level":    l.level,
                "event":    l.event,
                "message":  l.message,
                "agent_id": l.agent_id,
                "payload":  l.payload,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    return result


# ════════════════════════════════════════════════════════
# LIST
# ════════════════════════════════════════════════════════
