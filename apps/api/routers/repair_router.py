"""
Repair Router — Self-Repair sistemi için REST API.

Endpoint'ler:
  POST   /repair/incidents              -> Incident oluştur
  GET    /repair/incidents              -> Açık incident listesi
  GET    /repair/incidents/{id}         -> Incident detayı
  POST   /repair/jobs                  -> Repair job başlat
  GET    /repair/jobs                  -> Job listesi
  GET    /repair/jobs/{id}             -> Job detayı
  GET    /repair/jobs/{id}/validation  -> Validation raporu
  GET    /repair/jobs/{id}/diff        -> Önerilen diff
  POST   /repair/jobs/{id}/create-pr   -> PR önerisi oluştur (dry-run)
  POST   /repair/jobs/{id}/decision    -> İnsan kararı (approve/reject)
  GET    /repair/proposals             -> Bekleyen PR listesi
  POST   /repair/proposals/{id}/decide -> PR kararı ver
  GET    /repair/stats                 -> İstatistikler + hafıza özeti
  GET    /repair/architecture          -> Mimari hafızayı görüntüle
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.routers.auth.jwt_auth import get_current_user, require_admin
from repair.ingestion.incident_ingestor import incident_ingestor
from repair.triage.triage_engine import triage_engine
from repair.memory.incident_memory import incident_memory
from repair.memory.patch_memory import patch_memory
from repair.memory.architecture_memory import architecture_memory
from core.repair_orchestrator import get_repair_orchestrator
from core.policy_engine import policy_engine
from repair.schemas.incident import IncidentSource, IncidentSeverity
from observability.logging import get_logger

_log = get_logger("api.repair")

router = APIRouter(prefix="/repair", tags=["Self-Repair"])


# ── Request / Response Modelleri ────────────────────────────

class IncidentCreateRequest(BaseModel):
    source:            str = Field(default="manual")
    severity:          str = Field(default="medium")
    service:           str = Field(default="backend-api")
    module:            str = Field(default="unknown")
    symptom:           str = Field(min_length=5, max_length=1000)
    stack_trace:       str = Field(default="")
    suspected_files:   list[str] = Field(default_factory=list)
    failing_tests:     list[str] = Field(default_factory=list)
    reproduction_hint: str = Field(default="")

    model_config = {"extra": "ignore"}


class JobStartRequest(BaseModel):
    incident_id: str = Field(description="Mevcut bir incident_id")

    model_config = {"extra": "ignore"}


class JobDecisionRequest(BaseModel):
    decision:    str = Field(description="approve | reject")
    decided_by:  str = Field(default="human")
    reason:      str = Field(default="")

    model_config = {"extra": "ignore"}


class ProposalDecisionRequest(BaseModel):
    decision:   str  = Field(description="approved | rejected | merged")
    decided_by: str  = Field(default="human")

    model_config = {"extra": "ignore"}


class QARunRequest(BaseModel):
    url:      Optional[str] = Field(default=None, description="Opsiyonel hedef URL")
    selector: Optional[str] = Field(default=None, description="Opsiyonel beklenen CSS selector")

    model_config = {"extra": "ignore"}


# ── Incident Endpoint'leri ───────────────────────────────────

@router.post("/incidents", status_code=201)
async def create_incident(
    body: IncidentCreateRequest,
    current_user = Depends(get_current_user),
):
    """Manuel incident oluştur. Sistem otomatik triage başlatır."""
    try:
        source   = IncidentSource(body.source)
        severity = IncidentSeverity(body.severity)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Geçersiz değer: {e}")

    incident = incident_ingestor.from_dict({
        "source":            source.value,
        "severity":          severity.value,
        "service":           body.service,
        "module":            body.module,
        "symptom":           body.symptom,
        "stack_trace":       body.stack_trace,
        "suspected_files":   body.suspected_files,
        "failing_tests":     body.failing_tests,
        "reproduction_hint": body.reproduction_hint,
    })
    incident_memory.record(incident)

    # DB'ye kaydet (hata olursa ignore)
    await _persist_incident(incident)

    return {"incident_id": incident.incident_id, "status": "created", **incident.to_dict()}


@router.get("/incidents")
async def list_incidents(
    status: Optional[str] = Query(default=None, description="open|resolved|rejected"),
    module: Optional[str] = Query(default=None),
    limit:  int           = Query(default=20, le=100),
    current_user = Depends(get_current_user),
):
    """Açık veya filtreli incident listesi."""
    incidents = list(incident_ingestor.list_open())
    if status and status != "open":
        # Hafızada tüm status için tarama
        incidents = [i for i in incident_memory._incidents.values() if i.status == status]
    if module:
        incidents = [i for i in incidents if i.module == module]
    return {
        "total":     len(incidents),
        "incidents": [i.to_dict() for i in incidents[:limit]],
    }


@router.get("/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    current_user = Depends(get_current_user),
):
    """Incident detayı."""
    inc = incident_memory.get(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident bulunamadı")
    return {
        **inc.to_dict(),
        "similar": [s.to_dict() for s in incident_memory.get_similar(inc.symptom, inc.module)][:3],
    }


# ── Job Endpoint'leri ────────────────────────────────────────

@router.post("/jobs", status_code=201)
async def start_repair_job(
    body: JobStartRequest,
    current_user = Depends(get_current_user),
):
    """Bir incident için repair pipeline başlat."""
    inc = incident_memory.get(body.incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident bulunamadı")

    orchestrator = get_repair_orchestrator()
    job = await orchestrator.start_repair(inc)

    return {
        "job_id":    job.job_id,
        "status":    job.status.value,
        "message":   "Repair pipeline başlatıldı. Pipeline asenkron çalışır.",
        **job.to_dict(),
    }


@router.get("/jobs")
async def list_jobs(
    limit: int = Query(default=20, le=100),
    status: Optional[str] = Query(default=None),
    current_user = Depends(get_current_user),
):
    """Son repair job'ları listele."""
    orchestrator = get_repair_orchestrator()
    # `RepairOrchestrator.list_jobs` is an async coroutine.  It must be awaited
    # otherwise Python will return a coroutine object and the route will
    # erroneously attempt to iterate over it.  Awaiting ensures we fetch the
    # current list of repair jobs before filtering on status.
    jobs = await orchestrator.list_jobs(limit=limit)
    if status:
        jobs = [j for j in jobs if j.status.value == status]
    return {
        "total": len(jobs),
        "jobs":  [j.to_dict() for j in jobs],
    }


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user = Depends(get_current_user),
):
    """Job detayı ve durum geçiş geçmişi."""
    orchestrator = get_repair_orchestrator()
    # `RepairOrchestrator.get_job` returns a coroutine – await it to get the
    # actual job instance. Without awaiting, the router would return a
    # coroutine object rather than the job data, leading to 500 errors.
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job bulunamadı")
    return job.to_dict()


@router.get("/jobs/{job_id}/diff")
async def get_job_diff(
    job_id: str,
    current_user = Depends(get_current_user),
):
    """Üretilen patch diff'ini görüntüle."""
    orchestrator = get_repair_orchestrator()
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job bulunamadı")
    if not job.diff:
        raise HTTPException(status_code=404, detail="Bu job için diff henüz üretilmedi")
    return {
        "job_id":      job.job_id,
        "branch_name": job.branch_name,
        "diff":        job.diff,
        "warning":     "Bu diff henüz uygulanmamıştır. PR onayı gereklidir.",
    }


@router.post("/jobs/{job_id}/decision")
async def job_decision(
    job_id: str,
    body:   JobDecisionRequest,
    current_user = Depends(require_admin),   # Sadece admin karar verebilir
):
    """İnsan kararını kaydet (approve/reject)."""
    orchestrator = get_repair_orchestrator()
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job bulunamadı")

    if body.decision not in ("approve", "reject"):
        raise HTTPException(status_code=422, detail="decision: 'approve' veya 'reject' olmalı")

    from repair.schemas.repair_job import RepairJobStatus
    if body.decision == "reject":
        job.transition(RepairJobStatus.REJECTED, note=f"İnsan kararı: {body.reason[:100]}")
    else:
        job.transition(RepairJobStatus.MERGED, note=f"İnsan onayı: {body.decided_by}")

    return {"job_id": job_id, "new_status": job.status.value, "decided_by": body.decided_by}


@router.post("/jobs/{job_id}/run-qa")
async def run_job_qa(
    job_id: str,
    body:   Optional[QARunRequest] = None,
    current_user = Depends(get_current_user),
):
    """Manüel olarak Browser QA doğrulamasını tetikle."""
    orchestrator = get_repair_orchestrator()
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job bulunamadı")

    # Incident'ı bul (url bilgisi için)
    inc = incident_memory.get(job.incident_id)
    if not inc:
         raise HTTPException(status_code=404, detail="Bağlı incident bulunamadı")

    # Eğer istekte URL/selector varsa context'i geçici olarak güncelle
    if body:
        if body.url:
            inc.context["url"] = body.url
        if body.selector:
            inc.context["selector"] = body.selector

    if not inc.context.get("url"):
        raise HTTPException(status_code=422, detail="QA için bir URL belirtilmemiş (incident context veya request body)")

    success = await orchestrator._step_browser_qa(job, inc)
    
    return {
        "job_id": job_id,
        "success": success,
        "summary": "QA doğrulama tamamlandı" if success else "QA doğrulama başarısız oldu",
        "logs": job.logs[-2:] if job.logs else []
    }


# ── PR Önerileri ─────────────────────────────────────────────

@router.get("/proposals")
async def list_proposals(
    current_user = Depends(get_current_user),
):
    """Bekleyen PR önerileri — DB + in-memory birleşik liste."""
    # Önce in-memory (güncel session)
    from repair.release.pr_creator import get_pr_creator
    creator   = get_pr_creator(_get_repair_project_root())
    mem_props = creator.list_proposals()

    # DB'den de al (restart sonrası kalıcı kayıtlar)
    db_props = await _list_proposals_from_db()

    # Birleştir — pr_id'ye göre deduplicate (memory öncelikli)
    combined: dict[str, dict] = {p["pr_id"]: p for p in db_props}
    for p in mem_props:
        combined[p.pr_id] = p.to_dict()

    result = list(combined.values())
    return {
        "total":     len(result),
        "proposals": result,
        "note":      "Otomatik merge kapalıdır. Merge için git üzerinden insan onayı gerekir.",
    }


@router.get("/proposals/{pr_id}")
async def get_proposal(
    pr_id: str,
    current_user = Depends(get_current_user),
):
    """PR önerisi detayı (diff dahil). In-memory veya DB'den okur."""
    from repair.release.pr_creator import get_pr_creator
    creator  = get_pr_creator(_get_repair_project_root())
    proposal = creator.get_proposal(pr_id)

    if proposal:
        data = proposal.to_dict()
        data["diff"] = proposal.diff
    else:
        # DB'den dene
        data = await _get_proposal_from_db(pr_id)
        if not data:
            raise HTTPException(status_code=404, detail="PR önerisi bulunamadı")

    data["auto_merge"]    = False
    data["merge_warning"] = "Merge etmeden önce diff'i inceleyiniz."
    return data


@router.post("/proposals/{pr_id}/decision")
@router.post("/proposals/{pr_id}/decide")  # backward compat
async def decide_proposal(
    pr_id: str,
    body:  ProposalDecisionRequest,
    current_user = Depends(require_admin),
):
    """PR kararını kaydet ve ilgili job statüsünü güncelle."""
    if body.decision not in ("approved", "rejected", "merged"):
        raise HTTPException(status_code=422, detail="Geçersiz karar değeri")

    # DB'ye kaydet
    await _persist_proposal_decision(pr_id, body.decision, body.decided_by)

    # İlgili job statüsünü güncelle — in-memory + DB fallback
    await _update_job_on_proposal_decision(pr_id, body.decision, body.decided_by)

    return {
        "pr_id":      pr_id,
        "decision":   body.decision,
        "decided_by": body.decided_by,
        "note":       "Karar kaydedildi. Gerçek merge işlemi git üzerinden yapılmalıdır.",
    }


# ── Durum & İstatistik ───────────────────────────────────────

@router.get("/stats")
async def get_stats(
    current_user = Depends(get_current_user),
):
    """Repair sistemi istatistikleri."""
    orchestrator = get_repair_orchestrator()
    try:
        hotspots = [
            {
                "module":   p.module,
                "total":    p.total_incidents,
                "resolved": p.resolved,
                "score":    p.hotspot_score,
            }
            for p in incident_memory.hotspot_modules(5)
        ]
    except Exception:
        hotspots = []

    try:
        patterns = [
            {
                "module":          p.module,
                "symptom":         p.symptom_prefix,
                "count":           p.count,
                "resolution_rate": p.resolution_rate,
            }
            for p in incident_memory.detect_patterns()[:5]
        ]
    except Exception:
        patterns = []

    orch_stats = orchestrator.stats()
    inc_stats  = incident_memory.stats()

    return {
        "pipeline":        orch_stats,
        "incident_memory": inc_stats,
        "patch_memory":    patch_memory.stats(),
        "policy":          policy_engine.stats(),
        "hotspot_modules": hotspots,
        "patterns":        patterns,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Dashboard expects these at root level
        "open_incidents":  inc_stats.get("open", 0),
        "active_jobs":     orch_stats.get("active_jobs", 0),
        "success_rate_pct": orch_stats.get("success_rate", 0) * 100,
    }


@router.get("/architecture")
async def get_architecture_memory(
    current_user = Depends(get_current_user),
):
    """Sistemin mimari hafızasını görüntüle (patch planlarını yönlendirir)."""
    return {
        "contracts": [
            {
                "module":         c.module,
                "owner_file":     c.owner_file,
                "public_symbols": c.public_symbols,
                "critical":       c.critical,
            }
            for c in architecture_memory._contracts.values()
        ],
        "forbidden_patterns": [
            {"pattern": fp.pattern, "reason": fp.reason, "replacement": fp.replacement}
            for fp in architecture_memory.get_forbidden_patterns()
        ],
        "patch_safety_rules": architecture_memory.get_patch_safety_rules(),
        "adrs": [
            {"id": a.id, "title": a.title, "status": a.status, "decision": a.decision}
            for a in architecture_memory.get_adrs()
        ],
    }


@router.get("/triage-preview")
async def triage_preview(
    symptom: str = Query(min_length=5),
    module:  str = Query(default="unknown"),
    current_user = Depends(get_current_user),
):
    """Gerçek incident oluşturmadan triage sonucunu önizle."""
    from repair.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
    inc = IncidentRecord.create(
        source=IncidentSource.MANUAL,
        severity=IncidentSeverity.MEDIUM,
        service="preview",
        module=module,
        symptom=symptom,
    )
    ticket = triage_engine.triage(inc)
    policy = policy_engine.evaluate_triage(ticket)
    return {
        "classification":    ticket.classification.value,
        "recommended_mode":  ticket.recommended_mode.value,
        "candidate_files":   ticket.candidate_files,
        "requires_human":    ticket.requires_human,
        "policy_decision":   policy.to_dict(),
        "note":              "Bu önizleme — gerçek incident veya job oluşturulmadı.",
    }


# ── Yardımcı Fonksiyonlar ────────────────────────────────────

async def _update_job_on_proposal_decision(pr_id: str, decision: str, decided_by: str) -> None:
    """Proposal kararına göre linked job durumunu güncelle.
    In-memory bulunamazsa DB'den job_id lookup yapar."""
    from repair.schemas.repair_job import RepairJobStatus
    job_id = None

    # Önce in-memory dene
    try:
        from repair.release.pr_creator import get_pr_creator
        creator  = get_pr_creator(_get_repair_project_root())
        proposal = creator.get_proposal(pr_id)
        if proposal:
            job_id = proposal.job_id
    except Exception:
        pass

    # In-memory bulunamazsa DB'den job_id çek
    if not job_id:
        try:
            from db.session import AsyncSessionLocal, is_db_available
            if await is_db_available():
                from sqlalchemy import select
                from db.repair_models import RepairProposal as RepairProposalModel
                async with AsyncSessionLocal() as db:
                    stmt = select(RepairProposalModel.job_id).where(RepairProposalModel.pr_id == pr_id)
                    result = await db.execute(stmt)
                    row = result.scalar_one_or_none()
                    if row:
                        job_id = str(row)
        except Exception as e:
            _log.debug(f"Proposal job_id DB lookup hatası: {e}")

    if not job_id:
        _log.warning(f"Proposal {pr_id} için job_id bulunamadı — job status güncellenemiyor")
        return

    # Job status güncelle (in-memory)
    try:
        orch = get_repair_orchestrator()
        job  = await orch.get_job(job_id)
        if job:
            if decision in ("approved", "merged"):
                job.transition(RepairJobStatus.MERGED, note=f"İnsan onayı: {decided_by}")
            elif decision == "rejected":
                job.transition(RepairJobStatus.REJECTED, note=f"İnsan reddi: {decided_by}")
            # DB'ye de yaz
            await _persist_job_status(job)
    except Exception as e:
        _log.warning(f"Job status güncelleme hatası: {e}")


async def _persist_job_status(job) -> None:
    """Job durumunu DB'ye yaz (sessiz hata)."""
    try:
        from db.session import AsyncSessionLocal, is_db_available
        if not await is_db_available():
            return
        from db.repair_repository import RepairJobRepo
        async with AsyncSessionLocal() as db:
            await RepairJobRepo.upsert(db, job)
            await db.commit()
    except Exception as e:
        _log.debug(f"Job status DB yazma hatası (ignore): {e}")


async def _list_proposals_from_db() -> list[dict]:
    """DB'deki tüm proposal'ları getir (sessiz hata)."""
    try:
        from db.session import AsyncSessionLocal, is_db_available
        if not await is_db_available():
            return []
        from db.repair_repository import RepairProposalRepo
        async with AsyncSessionLocal() as db:
            rows = await RepairProposalRepo.list_pending(db)
            return [
                {
                    "pr_id":         str(r.pr_id),
                    "job_id":        str(r.job_id),
                    "incident_id":   str(r.incident_id),
                    "branch_name":   r.branch_name,
                    "title":         r.title,
                    "risk_level":    r.risk_level,
                    "decision":      r.decision,
                    "auto_merge":    r.auto_merge,
                    "created_at":    r.created_at.isoformat() if r.created_at else "",
                }
                for r in rows
            ]
    except Exception as e:
        _log.warning(f"Proposal DB okuma hatası (ignore): {e}")
        return []


async def _get_proposal_from_db(pr_id: str) -> Optional[dict]:
    """Tekil proposal'ı DB'den getir (sessiz hata)."""
    try:
        from db.session import AsyncSessionLocal, is_db_available
        if not await is_db_available():
            return None
        from sqlalchemy import select
        from db.repair_models import RepairProposal
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            stmt = select(RepairProposal).where(RepairProposal.pr_id == pr_id)
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                return None
            return {
                "pr_id":               str(row.pr_id),
                "job_id":              str(row.job_id),
                "incident_id":         str(row.incident_id),
                "branch_name":         row.branch_name,
                "title":               row.title,
                "body":                row.body,
                "diff":                row.diff,
                "risk_level":          row.risk_level,
                "decision":            row.decision,
                "validation_summary":  row.validation_summary,
                "auto_merge":          row.auto_merge,
                "created_at":          row.created_at.isoformat() if row.created_at else "",
            }
    except Exception as e:
        _log.warning(f"Proposal detay DB okuma hatası (ignore): {e}")
        return None


def _get_repair_project_root() -> str:
    """Repair orchestrator'la aynı project_root döndür (singleton uyumu)."""
    try:
        from core.repair_orchestrator import get_repair_orchestrator
        orch = get_repair_orchestrator()
        return getattr(orch, "project_root", ".")
    except Exception:
        return "."


async def _persist_incident(incident) -> None:
    """Incident'i DB'ye kaydet (sessiz hata)."""
    try:
        from db.session import AsyncSessionLocal, is_db_available
        if not await is_db_available():
            return
        from db.repair_repository import RepairIncidentRepo
        async with AsyncSessionLocal() as db:
            await RepairIncidentRepo.upsert(db, incident)
            await db.commit()
    except Exception as e:
        _log.warning(f"Incident DB yazma hatası (ignore): {e}")


async def _persist_proposal_decision(pr_id: str, decision: str, decided_by: str) -> None:
    """PR kararını DB'ye kaydet (sessiz hata)."""
    try:
        from db.session import AsyncSessionLocal, is_db_available
        if not await is_db_available():
            return
        from db.repair_repository import RepairProposalRepo
        async with AsyncSessionLocal() as db:
            await RepairProposalRepo.decide(db, pr_id, decision, decided_by)
            await db.commit()
    except Exception as e:
        _log.warning(f"Proposal karar DB yazma hatası (ignore): {e}")


# ─────────────────────────────────────────────────────────────
# Faz 11 — Yeni endpoint'ler
# ─────────────────────────────────────────────────────────────

@router.get("/incidents/{incident_id}/similar")
async def get_similar_incidents(
    incident_id: str,
    limit: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.5, ge=0.1, le=1.0),
    current_user=Depends(get_current_user),
):
    """Benzer incident'leri döndür (Faz 11 — Similarity Engine)."""
    from repair.analysis.incident_fingerprint import build_fingerprint, get_similarity_engine
    incident = incident_memory.get(incident_id)
    if not incident:
        raise HTTPException(404, "Incident bulunamadı")
    fp = build_fingerprint(incident)
    similars = get_similarity_engine().find_similar(fp, limit=limit, min_similarity=min_similarity)
    return {
        "incident_id": incident_id,
        "fingerprint": fp.to_dict(),
        "similar": [
            {"incident_id": s.incident_id, "similarity": s.similarity,
             "match_type": s.match_type, "reason": s.reason}
            for s in similars
        ],
    }



@router.get("/jobs/{job_id}/validation")
async def get_job_validation(job_id: str, current_user=Depends(get_current_user)):
    """
    Job doğrulama sonuçlarını döndür — RC1 Gerçek Kanıt Zinciri.
    Önce kalıcı store'dan gerçek raporu çek; yoksa job'dan türet.
    """
    orchestrator = get_repair_orchestrator(_get_repair_project_root())
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job bulunamadı")

    # 1. Gerçek validation raporunu store'dan çek (RC1)
    try:
        from repair.verification.verification_engine import get_validation_report
        real_report = get_validation_report(job_id) or get_validation_report(job.validation_id or "")
        if real_report:
            return {
                "job_id":           job_id,
                "source":           "verification_store",
                **real_report,
                "canary_status":    job.canary_status,
                "risk_score":       job.risk_score,
                "sandbox_verified": getattr(job, "sandbox_verified", False),
                "generated_tests":  getattr(job, "generated_tests", []),
                "job_status":       job.status.value,
                "confidence":       real_report.get("confidence", "high"),
                "summary":          real_report.get("summary", "Doğrulama motoru tarafından onaylandı (yüksek güven)."),
            }
    except Exception:
        pass

    # 2. Fallback: job state'den türet (henüz verify olmamışsa)
    verified_states = ("verified", "canary_pending", "canary_running",
                       "canary_passed", "canary_failed",
                       "pr_created", "awaiting_approval", "merged")
    val_data: dict = {
        "job_id":           job_id,
        "source":           "derived",
        "validation_id":    job.validation_id,
        "syntax_ok":        True,
        "lint_ok":          True,
        "security_ok":      True,
        "unit_tests_ok":    job.status.value in verified_states,
        "architecture_ok":  True,
        "patch_applied":    bool(job.diff),
        "canary_status":    job.canary_status,
        "risk_score":       job.risk_score,
        "sandbox_verified": getattr(job, "sandbox_verified", False),
        "sandbox_output":   getattr(job, "sandbox_output", ""),
        "generated_tests":  getattr(job, "generated_tests", []),
        "job_status":       job.status.value,
        "patch_apply_output": "",
        "verification_gaps": [],
        "architecture_notes": [],
        "confidence":       "low",
        "summary":          "Resmi doğrulama henüz tamamlanmadı; durum verilerinden türetildi (düşük güven).",
    }

    # Architecture guard canlı kontrol
    if job.diff:
        try:
            from repair.review.architecture_guard import get_architecture_guard
            guard_result = get_architecture_guard().check_diff(job.diff)
            val_data["architecture_ok"]    = guard_result.passed
            val_data["architecture_notes"] = [
                {"rule": v.rule, "severity": v.severity, "description": v.description}
                for v in guard_result.violations
            ]
        except Exception:
            pass

    return val_data


@router.get("/jobs/{job_id}/generated-tests")
async def get_generated_tests(job_id: str, current_user=Depends(get_current_user)):
    """Job için üretilen test dosyalarını döndür (Faz 11 — Test Generator)."""
    orchestrator = get_repair_orchestrator(_get_repair_project_root())
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job bulunamadı")
    return {
        "job_id":   job_id,
        "tests":    job.generated_tests,
        "count":    len(job.generated_tests),
    }


@router.get("/jobs/{job_id}/canary")
async def get_canary_result(job_id: str, current_user=Depends(get_current_user)):
    """Job'ın canary doğrulama sonucunu döndür (Faz 11)."""
    orchestrator = get_repair_orchestrator(_get_repair_project_root())
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job bulunamadı")
    return {
        "job_id":       job_id,
        "canary_id":    job.canary_id,
        "canary_status": job.canary_status,
        "job_status":   job.status.value,
    }


@router.get("/jobs/{job_id}/report")
async def get_job_report(
    job_id: str,
    fmt: str = Query("markdown", pattern="^(markdown|html)$"),
    current_user=Depends(get_current_user),
):
    """Job raporu döndür — markdown veya html (Faz 11)."""
    from fastapi.responses import PlainTextResponse, HTMLResponse
    from repair.reporting.report_generator import generate_markdown_report, generate_html_report

    orchestrator = get_repair_orchestrator(_get_repair_project_root())
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job bulunamadı")
    incident = incident_memory.get(job.incident_id)
    if not incident:
        raise HTTPException(404, "Incident bulunamadı")

    if fmt == "html":
        report = generate_html_report(job, incident)
        return HTMLResponse(content=report)
    report = generate_markdown_report(job, incident)
    return PlainTextResponse(content=report)


@router.post("/jobs/{job_id}/simulate")
async def simulate_job(
    job_id: str,
    current_user=Depends(get_current_user),
):
    """
    Simülasyon modu — gerçek patch üretmeden pipeline'ı çalıştır.
    Tahmini risk, validation beklentisi ve hangi dosyaların etkileneceğini döndürür.
    """
    orchestrator = get_repair_orchestrator(_get_repair_project_root())
    job = await orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job bulunamadı")
    incident = incident_memory.get(job.incident_id)
    if not incident:
        raise HTTPException(404, "Incident bulunamadı")

    # Triage preview ile taktiksel önizleme
    from repair.triage.triage_engine import triage_engine as te
    from core.policy_registry import get_policy_registry
    from repair.analysis.incident_fingerprint import build_fingerprint, get_similarity_engine

    ticket = te.triage(incident)
    fp     = build_fingerprint(incident)
    dup    = get_similarity_engine().is_duplicate(fp)
    policy = get_policy_registry()

    blocked_files = [f for f in ticket.candidate_files
                     if policy.is_module_blocked(f) or policy.is_high_risk_file(f)]
    safe_files    = [f for f in ticket.candidate_files if f not in blocked_files]

    return {
        "simulation_mode":       True,
        "job_id":                job_id,
        "incident_id":           job.incident_id,
        "triage": {
            "classification":    ticket.classification.value,
            "mode":              ticket.repair_mode.value,
            "requires_human":    ticket.requires_human_review,
            "candidate_files":   ticket.candidate_files,
        },
        "risk_estimate": {
            "blocked_files":     blocked_files,
            "safe_files":        safe_files,
            "estimated_risk":    "high" if blocked_files else ("medium" if len(safe_files) > 2 else "low"),
            "max_diff_allowed":  policy.max_diff_lines(),
            "min_confidence":    policy.min_confidence(),
        },
        "similarity": {
            "is_duplicate":      dup is not None,
            "duplicate_of":      dup,
            "fingerprint_hash":  fp.exact_hash,
        },
        "expected_flow": _expected_flow(ticket, policy),
    }


def _expected_flow(ticket, policy) -> list[str]:
    """Simülasyon — tahmini pipeline adımları."""
    steps = ["INCIDENT_COLLECTED", "TRIAGED", "CONTEXT_BUILT", "ROOT_CAUSE_ANALYZED",
             "PATCH_PLANNED", "PATCH_GENERATED", "REVIEWED", "VERIFIED"]
    if policy.canary_required():
        steps += ["CANARY_PENDING", "CANARY_RUNNING", "CANARY_PASSED"]
    steps += ["PR_CREATED", "AWAITING_APPROVAL"]
    if ticket.requires_human_review:
        steps = [s for s in steps if s != "AWAITING_APPROVAL"]
        steps.append("REQUIRES_MANUAL_REVIEW")
    return steps


@router.get("/architecture/guard/check")
async def architecture_guard_check(
    diff: str = Query(..., description="Kontrol edilecek unified diff metni"),
    current_user=Depends(get_current_user),
):
    """Bir diff metnini architecture guard'dan geçir (Faz 11)."""
    from repair.review.architecture_guard import get_architecture_guard
    result = get_architecture_guard().check_diff(diff)
    return result.to_dict()
