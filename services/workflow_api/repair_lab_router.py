
"""
services/workflow_api/repair_lab_router.py — Phase 28
Exposes Laboratory, Tournament, and Tuning data to the Refine Dashboard.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# FastAPI imports
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import desc, func, select

from libs.db.models.learning_models import NegativePatternMemory, StrategyMemory
from libs.db.models.repair_models import (
    RepairBenchmarkRun,
    RepairCandidate,
    RepairMemory,
    RepairTournament,
    SelfTuningSuggestion,
    UIRepairPRFinding,
    VerifierResult,
    UIRepairPRReview,
)
from libs.db.session import AsyncSessionLocal
from services.improve.repair_bench import RepairBenchService
from services.orchestration.application.sovereign_cortex import get_sovereign_cortex

router = APIRouter(tags=["Autonomous Repair Lab"])
# Logger init
logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS_DIR = REPO_ROOT / "repair_outputs"
REPAIR_ARTIFACT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".zip", ".json", ".md", ".log", ".diff"}
REPAIR_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# ── Response Schemas ──────────────────────────────────────────────────────────

class CandidateSummary(BaseModel):
    strategy: str
    score: float
    status: str
    type: str
    score_breakdown: dict[str, Any] | None = None

class TournamentOut(BaseModel):
    id: str
    incident_id: str
    winner_id: str | None
    winner_score: float
    total_candidates: int
    created_at: datetime
    candidates: list[CandidateSummary] = []

class SuggestionUpdate(BaseModel):
    status: str # approved | rejected

class TuningSuggestionOut(BaseModel):
    id: str
    parameter: str
    current_value: float
    proposed_value: float
    reason: str
    impact: str
    status: str
    created_at: datetime

class LabRunRequest(BaseModel):
    diagnostic_id: str | None = None
    source: str | None = "repair_lab"

# ── PR-Agent Schemas (Phase 32) ─────────────────────────────────────────────

class PRAgentActionRequest(BaseModel):
    pr_url: str

class PRAgentFindingOut(BaseModel):
    id: str
    file_path: str | None = None
    line_number: int | None = None
    severity: str
    category: str
    message: str
    suggestion: str | None = None

class PRAgentReviewOut(BaseModel):
    review_id: str
    case_id: str
    pr_url: str
    status: str
    summary: str
    governance_decision: str | None = None
    findings: list[PRAgentFindingOut] = []
    created_at: datetime


def _safe_repair_artifact_path(incident_id: str, artifact_path: str) -> Path:
    incident_dir = (REPAIR_OUTPUTS_DIR / incident_id).resolve()
    candidate = (incident_dir / artifact_path).resolve()
    if incident_dir != candidate and incident_dir not in candidate.parents:
        raise HTTPException(status_code=400, detail="Artifact path escapes repair output scope.")
    if candidate.suffix.lower() not in REPAIR_ARTIFACT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Artifact type is not allowed.")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return candidate


def _artifact_url(incident_id: str, path: Path) -> str:
    incident_dir = REPAIR_OUTPUTS_DIR / incident_id
    rel_path = path.relative_to(incident_dir).as_posix()
    return f"/api/v1/repair-lab/artifacts/{incident_id}/{rel_path}"


def _load_draft_pr(incident_dir: Path) -> dict[str, Any]:
    draft_path = incident_dir / "draft_pr.json"
    if not draft_path.exists():
        return {}
    try:
        raw = json.loads(draft_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw["draft_pr_path"] = str(draft_path)
            return raw
    except Exception:
        logger.warning("Draft PR artifact could not be parsed: %s", draft_path)
    return {}


def _load_evidence_assets(incident_id: str, incident_dir: Path) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for artifact in sorted(incident_dir.rglob("*")):
        if not artifact.is_file() or artifact.suffix.lower() not in REPAIR_IMAGE_EXTENSIONS:
            continue
        try:
            stat = artifact.stat()
            assets.append(
                {
                    "name": artifact.name,
                    "path": str(artifact),
                    "url": _artifact_url(incident_id, artifact),
                    "kind": "image",
                    "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
        except Exception:
            continue
    return assets


def _load_self_repair_reports(limit: int = 20) -> list[dict[str, Any]]:
    if not REPAIR_OUTPUTS_DIR.exists():
        return []

    reports: list[dict[str, Any]] = []
    for report_path in REPAIR_OUTPUTS_DIR.glob("*/repair_report.json"):
        try:
            raw = json.loads(report_path.read_text(encoding="utf-8"))
            repair_case = raw.get("repair_case") or {}
            risk_decision = raw.get("risk_decision") or {}
            sandbox_result = raw.get("sandbox_result") or {}
            candidate = raw.get("candidate") or {}
            stat = report_path.stat()
            incident_id = repair_case.get("incident_id") or report_path.parent.name
            draft_pr = _load_draft_pr(report_path.parent)
            pr_url = draft_pr.get("pr_url") or draft_pr.get("html_url") or draft_pr.get("url")
            reports.append(
                {
                    "incident_id": incident_id,
                    "trace_id": repair_case.get("trace_id"),
                    "summary": repair_case.get("summary") or "",
                    "final_status": raw.get("final_status") or "UNKNOWN",
                    "risk_level": risk_decision.get("risk_level") or "UNKNOWN",
                    "risk_score": risk_decision.get("risk_score"),
                    "recommended_action": risk_decision.get("recommended_action"),
                    "tests_passed": bool(sandbox_result.get("tests_passed")),
                    "patch_applied": bool(sandbox_result.get("patch_applied")),
                    "suspected_files": repair_case.get("suspected_files") or [],
                    "changed_files": candidate.get("changed_files") or [],
                    "patch_path": candidate.get("patch_path"),
                    "pr_url": pr_url,
                    "pr_title": draft_pr.get("title"),
                    "branch_name": draft_pr.get("branch_name"),
                    "draft_pr_path": draft_pr.get("draft_pr_path"),
                    "evidence": _load_evidence_assets(incident_id, report_path.parent),
                    "report_path": str(report_path),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "source": "repair_outputs",
                }
            )
        except Exception:
            continue

    return sorted(reports, key=lambda item: item["updated_at"], reverse=True)[:limit]


def _load_taskflow_runs(limit: int = 20) -> list[dict[str, Any]]:
    if not REPAIR_OUTPUTS_DIR.exists():
        return []

    runs: list[dict[str, Any]] = []
    for trace_path in REPAIR_OUTPUTS_DIR.glob("*/taskflow_trace.json"):
        try:
            raw = json.loads(trace_path.read_text(encoding="utf-8"))
            workflow_run = raw.get("workflow_run") if isinstance(raw.get("workflow_run"), dict) else {}
            steps = workflow_run.get("steps") if isinstance(workflow_run.get("steps"), list) else []
            events = workflow_run.get("events") if isinstance(workflow_run.get("events"), list) else []
            metrics = raw.get("metrics") if isinstance(raw.get("metrics"), list) else []
            artifacts = workflow_run.get("artifacts") if isinstance(workflow_run.get("artifacts"), list) else []
            step_statuses = [str(step.get("status") or "UNKNOWN") for step in steps if isinstance(step, dict)]
            gate_waiting = any(
                isinstance(event, dict) and event.get("event_name") == "taskflow.gate.waiting"
                for event in events
            )
            failed_steps = [
                str(step.get("step_id"))
                for step in steps
                if isinstance(step, dict) and str(step.get("status") or "").upper() in {"FAILED", "BLOCKED"}
            ]
            stat = trace_path.stat()
            runs.append(
                {
                    "incident_id": workflow_run.get("incident_id") or trace_path.parent.name,
                    "trace_id": workflow_run.get("trace_id"),
                    "workflow_id": workflow_run.get("workflow_id") or "unknown",
                    "workflow_name": workflow_run.get("workflow_name") or "",
                    "status": workflow_run.get("status") or "UNKNOWN",
                    "current_step": workflow_run.get("current_step"),
                    "final_decision": workflow_run.get("final_decision"),
                    "risk_score": workflow_run.get("risk_score"),
                    "step_count": len(steps),
                    "succeeded_step_count": sum(1 for status_name in step_statuses if status_name == "SUCCEEDED"),
                    "skipped_step_count": sum(1 for status_name in step_statuses if status_name == "SKIPPED"),
                    "failed_step_count": len(failed_steps),
                    "failed_steps": failed_steps,
                    "gate_waiting": gate_waiting,
                    "event_count": len(events),
                    "metric_count": len(metrics),
                    "artifact_count": len(artifacts),
                    "trace_path": str(trace_path),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "source": "taskflow_trace",
                }
            )
        except Exception:
            continue

    return sorted(runs, key=lambda item: item["updated_at"], reverse=True)[:limit]


def _normalize_improvement_status(meta: dict[str, Any], outcome: str | None) -> str:
    payload = meta.get("payload") if isinstance(meta.get("payload"), dict) else {}
    raw = str(meta.get("status") or payload.get("status") or outcome or "").lower()
    if raw in {"repaired", "completed", "success", "repaired_success"}:
        return "completed"
    if raw == "noop":
        return "completed"
    if raw in {"requires_operator_action", "operator_required", "action_required"}:
        return "action_required"
    return "failed"


def _lineage_to_improvement(item: Any) -> dict[str, Any]:
    meta = item.meta_data if isinstance(item.meta_data, dict) else {}
    payload = meta.get("payload") if isinstance(meta.get("payload"), dict) else {}
    trigger_event = item.trigger_event if isinstance(item.trigger_event, dict) else {}
    diagnostic_id = meta.get("diagnostic_id") or payload.get("diagnostic_id") or trigger_event.get("diagnostic_id")
    actions = meta.get("actions") or payload.get("actions") or []
    requires_operator_action = bool(
        meta.get("requires_operator_action")
        if "requires_operator_action" in meta
        else payload.get("requires_operator_action")
    )
    normalized_status = _normalize_improvement_status(meta, item.outcome)
    return {
        "id": str(item.id),
        "title": f"Runtime Repair: {diagnostic_id}" if diagnostic_id else f"Evolution: {item.component_name}",
        "component": item.component_name,
        "description": item.rationale,
        "status": normalized_status,
        "risk_level": meta.get("risk_level", "low"),
        "created_at": item.created_at,
        "diagnostic_id": diagnostic_id,
        "actions": actions,
        "requires_operator_action": requires_operator_action,
        "decision_type": item.decision_type,
        "outcome": item.outcome,
    }


async def _fetch_improvements(db, limit: int = 20) -> list[dict[str, Any]]:
    from libs.db.models.lineage_models import DecisionLineage

    q = select(DecisionLineage).order_by(desc(DecisionLineage.created_at)).limit(limit)
    res = await db.execute(q)
    return [_lineage_to_improvement(item) for item in res.scalars().all()]


@router.get("/improvements")
async def list_improvements(limit: int = 20):
    """Sistem tarafindan tespit edilen iyileshtirme firsatlarini ve otonom tamir kayitlarini listeler."""
    async with AsyncSessionLocal() as db:
        try:
            return await _fetch_improvements(db, limit=limit)
        except Exception as exc:
            logger.warning("Improvements list fallback: %s", exc)
            return []


@router.get("/self-repair-runs")
async def list_self_repair_runs(limit: int = 20):
    """Phase 1-3 self-repair JSON artifact runs visible to the dashboard."""
    return _load_self_repair_reports(limit=limit)


@router.get("/artifacts/{incident_id}/{artifact_path:path}")
async def get_repair_artifact(incident_id: str, artifact_path: str):
    """Serve allowlisted repair evidence artifacts from repair_outputs."""
    path = _safe_repair_artifact_path(incident_id, artifact_path)
    return FileResponse(path)


@router.get("/taskflow-runs")
async def list_taskflow_runs(limit: int = 20):
    """TaskFlow trace artifacts visible to the dashboard."""
    return _load_taskflow_runs(limit=limit)

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/benchmarks")
async def list_benchmarks(limit: int = 10):
    """Sistem performans benchmark geçmişini listeler."""
    async with AsyncSessionLocal() as db:
        try:
            q = select(RepairBenchmarkRun).order_by(desc(RepairBenchmarkRun.start_time)).limit(limit)
            res = await db.execute(q)
            runs = res.scalars().all()

            return [
                {
                    "id": str(r.run_id),
                    "name": f"Benchmark-Run-{r.run_id[:8]}",
                    "success_rate": r.success_rate,
                    "avg_score": r.avg_score,
                    "cases": r.total_cases,
                    "status": r.status,
                    "created_at": r.start_time
                }
                for r in runs
            ]
        except Exception as exc:
            logger.warning("Benchmarks list fallback: %s", exc)
            return []

@router.get("/tournaments", response_model=list[TournamentOut])
async def list_tournaments(limit: int = 20):
    """Gerçekleşen tamir turnuvalarını ve aday skorlarını listeler."""
    async with AsyncSessionLocal() as db:
        try:
            q = select(RepairTournament).order_by(desc(RepairTournament.created_at)).limit(limit)
            res = await db.execute(q)
            tournaments = res.scalars().all()

            results = []
            for t in tournaments:
                # Load candidates for this tournament
                cq = select(RepairCandidate).where(RepairCandidate.tournament_id == t.tournament_id)
                cres = await db.execute(cq)
                candidates = cres.scalars().all()

                results.append(TournamentOut(
                    id=t.tournament_id,
                    incident_id=t.incident_id,
                    winner_id=t.winner_candidate_id,
                    winner_score=t.winner_score,
                    total_candidates=t.total_candidates,
                    created_at=t.created_at,
                    candidates=[
                        CandidateSummary(
                            strategy=c.strategy,
                            score=c.final_score,
                            status=c.status,
                            type=c.candidate_type or "code",
                            score_breakdown=c.score_breakdown if hasattr(c, "score_breakdown") else None
                        )
                        for c in candidates
                    ]
                ))
            return results
        except Exception as exc:
            logger.warning("Tournaments list fallback: %s", exc)
            return []

@router.get("/learning/insights")
async def get_learning_insights():
    """Öğrenme motorundaki strateji hafızasını ve cezalandırılan paternleri döner."""
    async with AsyncSessionLocal() as db:
        try:
            # Fetch Trusted Strategies
            s_res = await db.execute(select(StrategyMemory).order_by(desc(StrategyMemory.trust_score)))
            memories = s_res.scalars().all()

            # Fetch Negative Patterns
            n_res = await db.execute(select(NegativePatternMemory).order_by(desc(NegativePatternMemory.penalty_weight)))
            negatives = n_res.scalars().all()

            return {
                "strategies": [
                    {
                        "name": m.strategy_name,
                        "trust_score": m.trust_score,
                        "state": m.state,
                        "success": m.success_count,
                        "rollbacks": m.rollback_count,
                        "avg_score": m.avg_verification_score
                    } for m in memories
                ],
                "penalized_patterns": [
                    {
                        "strategy": n.strategy_name,
                        "reason": n.failure_reason or n.rollback_reason,
                        "penalty": n.penalty_weight,
                        "occurrences": n.occurrence_count,
                        "blast_radius": n.blast_radius
                    } for n in negatives
                ]
            }
        except Exception as exc:
            logger.warning("Learning insights fallback: %s", exc)
            return {"strategies": [], "penalized_patterns": []}

@router.get("/verifiers/matrix")
async def get_verifier_matrix(tournament_id: str | None = None):
    """Verifier Mesh performans matrisini döner."""
    async with AsyncSessionLocal() as db:
        try:
            # If no tournament_id, take the latest one
            if not tournament_id:
                tid_q = select(RepairTournament.tournament_id).order_by(desc(RepairTournament.created_at)).limit(1)
                tournament_id = (await db.execute(tid_q)).scalar()
                if not tournament_id:
                    return {"verifiers": [], "candidates": []}

            # Get all candidates for the tournament
            cq = select(RepairCandidate).where(RepairCandidate.tournament_id == tournament_id)
            candidates = (await db.execute(cq)).scalars().all()

            # Get all verifiers used in this tournament
            c_ids = [c.candidate_id for c in candidates]
            vq = select(VerifierResult).where(VerifierResult.candidate_id.in_(c_ids))
            v_results = (await db.execute(vq)).scalars().all()

            verifiers = sorted(list(set(vr.verifier_name for vr in v_results)))

            matrix = []
            for c in candidates:
                row = {"name": c.strategy.capitalize(), "results": []}
                for v in verifiers:
                    # Find score for this candidate + verifier
                    match = next((vr.score for vr in v_results if vr.candidate_id == c.candidate_id and vr.verifier_name == v), 0.0)
                    row["results"].append(match)
                matrix.append(row)

            return {
                "tournament_id": tournament_id,
                "verifiers": verifiers,
                "candidates": matrix
            }
        except Exception as exc:
            logger.warning("Verifier matrix fallback: %s", exc)
            return {"verifiers": [], "candidates": []}

@router.get("/tuning/suggestions", response_model=list[TuningSuggestionOut])
async def get_tuning_suggestions():
    """Önerilen sistem ayar kalibrasyonlarını listeler."""
    async with AsyncSessionLocal() as db:
        try:
            q = select(SelfTuningSuggestion).order_by(desc(SelfTuningSuggestion.created_at))
            res = await db.execute(q)
            suggestions = res.scalars().all()

            return [
                TuningSuggestionOut(
                    id=s.suggestion_id,
                    parameter=s.parameter_name,
                    current_value=s.current_value,
                    proposed_value=s.proposed_value,
                    reason=s.reason,
                    impact=s.expected_impact or "N/A",
                    status=s.status,
                    created_at=s.created_at
                )
                for s in suggestions
            ]
        except Exception as exc:
            logger.warning("Tuning suggestions fallback: %s", exc)
            return []

@router.post("/tuning/suggestions/{suggestion_id}/apply")
async def apply_tuning_suggestion(suggestion_id: str, data: SuggestionUpdate):
    """Bir ayar önerisini onayla veya reddet."""
    async with AsyncSessionLocal() as db:
        q = select(SelfTuningSuggestion).where(SelfTuningSuggestion.suggestion_id == suggestion_id)
        suggestion = (await db.execute(q)).scalar_one_or_none()

        if not suggestion:
            raise HTTPException(status_code=404, detail="Öneri bulunamadı")

        suggestion.status = data.status
        await db.commit()
        return {"id": suggestion_id, "status": data.status}

@router.get("/verifiers")
async def get_verifiers_stats():
    """Verifier Mesh katmanlarının güvenilirlik ve performans verilerini döner."""
    async with AsyncSessionLocal() as db:
        try:
            q = select(VerifierResult).order_by(desc(VerifierResult.timestamp)).limit(500)
            results = (await db.execute(q)).scalars().all()

            # Aggregate stats by verifier
            stats = {}
            for r in results:
                name = r.verifier_name
                if name not in stats:
                    stats[name] = {"passed": 0, "total": 0, "latency": 0.0, "errors_blocked": 0}

                stats[name]["total"] += 1
                if r.passed:
                    stats[name]["passed"] += 1
                else:
                    stats[name]["errors_blocked"] += 1

                # Simulate latency if details.latency is missing
                latency = r.details.get("latency", 0.15) if isinstance(r.details, dict) else 0.15
                stats[name]["latency"] += latency

            return [
                {
                    "name": k,
                    "reliability": round(v["passed"] / v["total"], 2) if v["total"] > 0 else 0.0,
                    "precision": round(v["passed"] / v["total"], 2) if v["total"] > 0 else 0.0, # Simplified
                    "latency": f"{round((v['latency'] / v['total']) * 1000, 0)}ms" if v["total"] > 0 else "0ms",
                    "detected_errors": v["errors_blocked"]
                }
                for k, v in stats.items()
            ]
        except Exception as exc:
            logger.warning("Verifiers stats fallback: %s", exc)
            return []

@router.get("/memory/heatmaps")
async def get_repair_memory():
    """Tamir hafızasındaki başarı/başarısızlık yoğunluk haritasını döner."""
    async with AsyncSessionLocal() as db:
        try:
            q = select(RepairMemory).order_by(desc(RepairMemory.recorded_at)).limit(100)
            memories = (await db.execute(q)).scalars().all()

            # Aggregate by subsystem
            stats = {}
            for m in memories:
                ss = m.subsystem or "unknown"
                if ss not in stats:
                    stats[ss] = {"success": 0, "failure": 0, "total": 0}
                stats[ss]["total"] += 1
                if m.outcome == "success":
                    stats[ss]["success"] += 1
                else:
                    stats[ss]["failure"] += 1

            return [
                {"subsystem": k, "success": v["success"], "failure": v["failure"], "rate": round(v["success"]/v["total"], 2)}
                for k, v in stats.items()
            ]
        except Exception as exc:
            logger.warning("Repair memory heatmap fallback: %s", exc)
            return []

@router.get("/memory/details")
async def get_repair_memory_details(subsystem: str = Query(...), limit: int = 50):
    """Belirli bir alt sistem için detaylı tamir geçmişini döner."""
    async with AsyncSessionLocal() as db:
        try:
            q = (
                select(RepairMemory)
                .where(RepairMemory.subsystem == subsystem)
                .order_by(desc(RepairMemory.recorded_at))
                .limit(limit)
            )
            res = await db.execute(q)
            memories = res.scalars().all()

            return [
                {
                    "id": str(m.memory_id),
                    "incident_id": m.incident_id,
                    "outcome": m.outcome,
                    "failure_reason": m.failure_reason or "N/A",
                    "score": m.score,
                    "recorded_at": m.recorded_at,
                    "rejections": m.verifier_rejections or []
                }
                for m in memories
            ]
        except Exception as exc:
            logger.warning("Repair memory details fallback: %s", exc)
            return []

@router.post("/run")
async def trigger_lab_run(
    request: LabRunRequest | None = Body(default=None),
    cortex=Depends(get_sovereign_cortex),
):
    """Otonom tamir benchmark turunu başlatır."""
    from libs.db.models.lineage_models import DecisionLineage

    diagnostic_id = request.diagnostic_id if request else None
    source = request.source if request and request.source else "repair_lab"
    project_id = f"diagnostic:{diagnostic_id}" if diagnostic_id else "sovereign-agi"
    cluster_id = source if diagnostic_id else "local-lab"
    bench_svc = RepairBenchService(model_orch=cortex.model_orch)

    if diagnostic_id:
        async with AsyncSessionLocal() as db:
            db.add(
                DecisionLineage(
                    decision_type="REPAIR_LAB_TARGETED_RUN_REQUESTED",
                    component_name="repair_lab",
                    trigger_event={"diagnostic_id": diagnostic_id, "source": source},
                    rationale=f"Targeted repair benchmark requested for runtime diagnostic {diagnostic_id}.",
                    outcome="STARTED",
                    meta_data={
                        "source": source,
                        "diagnostic_id": diagnostic_id,
                        "success": True,
                        "status": "started",
                        "project_id": project_id,
                        "cluster_id": cluster_id,
                    },
                )
            )
            await db.commit()

    # Run in background to avoid timeout.
    asyncio.create_task(bench_svc.run_full_bench(project_id=project_id, cluster_id=cluster_id))
    return {
        "status": "started",
        "message": "Otonom benchmark turu arka planda baslatildi.",
        "diagnostic_id": diagnostic_id,
        "source": source,
    }


@router.get("/dashboard")
async def get_lab_dashboard():
    benchmarks = await list_benchmarks(limit=10)
    tournaments = await list_tournaments(limit=5)
    latest_tournament = tournaments[0].model_dump() if tournaments else None
    matrix = await get_verifier_matrix(tournament_id=latest_tournament["id"] if latest_tournament else None)
    async with AsyncSessionLocal() as db:
        try:
            improvements = await _fetch_improvements(db, limit=10)
        except Exception as exc:
            logger.warning("Dashboard improvements fallback: %s", exc)
            improvements = []
    self_repair_runs = _load_self_repair_reports(limit=10)
    taskflow_runs = _load_taskflow_runs(limit=10)
    return {
        "benchmarks": benchmarks,
        "tournament": latest_tournament,
        "matrix": matrix,
        "improvements": improvements,
        "self_repair_runs": self_repair_runs,
        "taskflow_runs": taskflow_runs,
    }


@router.get("/summary")
async def get_lab_summary():
    from libs.db.models.lineage_models import DecisionLineage

    async with AsyncSessionLocal() as db:
        benchmark_count = await db.scalar(select(func.count()).select_from(RepairBenchmarkRun)) or 0
        avg_success = await db.scalar(select(func.coalesce(func.avg(RepairBenchmarkRun.success_rate), 0.0))) or 0.0
        active_tournaments = await db.scalar(select(func.count()).select_from(RepairTournament)) or 0
        try:
            repair_rows = (
                await db.execute(
                    select(DecisionLineage).where(DecisionLineage.decision_type == "RUNTIME_REPAIR_ATTEMPT")
                )
            ).scalars().all()
            mapped = [_lineage_to_improvement(row) for row in repair_rows]
        except Exception as exc:
            logger.warning("Summary runtime repair fallback: %s", exc)
            mapped = []
        taskflow_runs = _load_taskflow_runs(limit=100)
        return {
            "total_benchmarks": int(benchmark_count),
            "success_rate": float(avg_success),
            "active_tournaments": int(active_tournaments),
            "runtime_repair_count": len(mapped),
            "action_required_count": sum(1 for item in mapped if item["status"] == "action_required"),
            "self_repair_run_count": len(_load_self_repair_reports(limit=100)),
            "taskflow_run_count": len(taskflow_runs),
            "taskflow_waiting_count": sum(1 for item in taskflow_runs if item["gate_waiting"]),
        }

@router.get("/evolution/feed")
async def get_evolution_feed(limit: int = 15):
    """Sistemin otonom gelişim günlüğünü (DecisionLineage) döner."""
    from libs.db.models.lineage_models import DecisionLineage
    async with AsyncSessionLocal() as db:
        try:
            q = select(DecisionLineage).where(DecisionLineage.decision_type == "SYSTEM_EVOLUTION").order_by(desc(DecisionLineage.created_at)).limit(limit)
            res = await db.execute(q)
            items = res.scalars().all()

            return [
                {
                    "id": str(i.id),
                    "component": i.component_name,
                    "rationale": getattr(i, "rationale", "N/A"),
                    "success": (i.meta_data or {}).get("success", False) if isinstance(i.meta_data, (dict, type(None))) else False,
                    "output": (i.meta_data or {}).get("output", "N/A") if isinstance(i.meta_data, (dict, type(None))) else "N/A",
                    "created_at": i.created_at
                }
                for i in items
            ]
        except Exception as exc:
            logger.warning("Evolution feed fallback: %s", exc)
            return []

@router.get("/evolution/status")
async def get_evolution_status():
    """Otonom gelişim döngüsünün durumunu döner."""
    from services.improve.evolution_orchestrator import evolution_orchestrator
    if not evolution_orchestrator:
        return {"is_running": False, "failure_counts": {}}

    return {
        "is_running": evolution_orchestrator.is_running,
        "failure_counts": evolution_orchestrator.failure_counter,
        "stuck_threshold": evolution_orchestrator.STUCK_THRESHOLD
    }

# �� PR-Agent Endpoints (Phase 32) ������������������������������������������

@router.post("/cases/{case_id}/pr-agent/describe")
async def pr_agent_describe(case_id: str, data: PRAgentActionRequest):
    from services.repair.pr_agent_adapter import PRAgentAdapter
    adapter = PRAgentAdapter()
    msg = await adapter.run_action(data.pr_url, "describe")
    return {"status": "ok", "message": msg}

@router.post("/cases/{case_id}/pr-agent/review")
async def pr_agent_review(case_id: str, data: PRAgentActionRequest):
    from services.repair.pr_agent_adapter import PRAgentAdapter
    adapter = PRAgentAdapter()
    msg = await adapter.run_action(data.pr_url, "review")
    return {"status": "ok", "message": msg}

@router.post("/cases/{case_id}/pr-agent/improve")
async def pr_agent_improve(case_id: str, data: PRAgentActionRequest):
    from services.repair.pr_agent_adapter import PRAgentAdapter
    adapter = PRAgentAdapter()
    msg = await adapter.run_action(data.pr_url, "improve")
    return {"status": "ok", "message": msg}

@router.post("/cases/{case_id}/pr-agent/full-review", response_model=PRAgentReviewOut)
async def pr_agent_full_review(case_id: str, data: PRAgentActionRequest):
    from services.repair.pr_agent_adapter import PRAgentAdapter
    adapter = PRAgentAdapter()
    result = await adapter.run_full_review_cycle(case_id, data.pr_url)

    return PRAgentReviewOut(
        review_id=result.review_id,
        case_id=case_id,
        pr_url=result.pr_url,
        status=result.status,
        summary=result.summary,
        governance_decision=result.governance_decision,
        findings=[
            PRAgentFindingOut(
                id=str(uuid.uuid4()),
                file_path=f.file_path,
                line_number=f.line_number,
                severity=f.severity,
                category=f.category,
                message=f.message,
                suggestion=f.suggestion
            ) for f in result.findings
        ],
        created_at=datetime.now(UTC)
    )

@router.get("/cases/{case_id}/pr-agent/findings", response_model=list[PRAgentReviewOut])
async def get_pr_agent_findings(case_id: str):
    async with AsyncSessionLocal() as db:
        q = select(UIRepairPRReview).where(UIRepairPRReview.case_id == case_id).order_by(desc(UIRepairPRReview.created_at))
        res = await db.execute(q)
        reviews = res.scalars().all()

        results = []
        for r in reviews:
            fq = select(UIRepairPRFinding).where(UIRepairPRFinding.review_id == r.review_id)
            fres = await db.execute(fq)
            findings = fres.scalars().all()

            results.append(PRAgentReviewOut(
                review_id=r.review_id,
                case_id=r.case_id,
                pr_url=r.pr_url,
                status=r.status,
                summary=r.summary,
                governance_decision=r.governance_decision,
                findings=[
                    PRAgentFindingOut(
                        id=str(f.finding_id),
                        file_path=f.file_path,
                        line_number=f.line_number,
                        severity=f.severity,
                        category=f.category,
                        message=f.message,
                        suggestion=f.suggestion
                    ) for f in findings
                ],
                created_at=r.created_at
            ))
        return results


@router.post("/cases/{case_id}/trigger-autonomous-repair")
async def trigger_autonomous_repair(case_id: str, target_url: str):
    from services.repair.ui_repair_orchestrator import UIRepairOrchestrator
    orchestrator = UIRepairOrchestrator()
    result = await orchestrator.run_full_repair_cycle(case_id, target_url)

    # Persistence for Phase 32: Save results to DB
    async with AsyncSessionLocal() as db:
        review_id = str(uuid.uuid4())
        review_obj = result.get("review")
        patch_obj = result.get("patch")

        # 1. Create Review Record
        review = UIRepairPRReview(
            review_id=review_id,
            case_id=case_id,
            pr_url=getattr(review_obj, 'pr_url', f"https://github.com/Sovereign-AGI/sovereign-control-plane/pull/{case_id}") if review_obj else f"https://github.com/Sovereign-AGI/sovereign-control-plane/pull/{case_id}",
            status=result.get("final_status", "PENDING"),
            summary=getattr(patch_obj, 'agent_summary', "Autonomous repair run completed.") if patch_obj else "Autonomous repair run completed.",
            governance_decision=result.get("final_status", "PENDING"),
            confidence_score=getattr(patch_obj, 'confidence', 0.0) if patch_obj else 0.0
        )
        db.add(review)

        # 2. Save Findings if available
        if review_obj and hasattr(review_obj, "findings"):
            for f in review_obj.findings:
                finding = UIRepairPRFinding(
                    finding_id=str(uuid.uuid4()),
                    review_id=review_id,
                    file_path=f.file_path,
                    line_number=f.line_number,
                    severity=f.severity,
                    category=f.category,
                    message=f.message,
                    suggestion=f.suggestion
                )
                db.add(finding)

        # 3. Save patch diff to disk for later application (Phase 32 Human-in-the-Loop)
        if patch_obj and hasattr(patch_obj, 'diff_text') and patch_obj.diff_text:
            try:
                patch_dir = REPAIR_OUTPUTS_DIR / case_id
                patch_dir.mkdir(parents=True, exist_ok=True)
                (patch_dir / "patch.diff").write_text(patch_obj.diff_text, encoding="utf-8")
                logger.info(f"Saved patch.diff for case {case_id}")
            except Exception as e:
                logger.error(f"Failed to save patch.diff for {case_id}: {e}")

        await db.commit()

    return {"status": "ok", "result": result, "review_id": review_id}

@router.post("/cases/{case_id}/apply-patch")
async def apply_patch(case_id: str):
    """
    Operator-Approved Patch Application.
    Applies the generated patch to the production source tree using 'git apply'.
    """
    import subprocess

    from libs.db.models.lineage_models import DecisionLineage

    # 1. Locate the patch diff
    patch_path = REPAIR_OUTPUTS_DIR / case_id / "patch.diff"
    if not patch_path.exists():
        # Fallback: check if it's in the report JSON
        report_path = REPAIR_OUTPUTS_DIR / case_id / "repair_report.json"
        if report_path.exists():
             try:
                 report_data = json.loads(report_path.read_text(encoding="utf-8"))
                 diff_text = report_data.get("candidate", {}).get("patch_diff") or report_data.get("patch", {}).get("diff_text")
             except Exception:
                 diff_text = None
        else:
             diff_text = None

        if not diff_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patch diff for case {case_id} not found."
            )
    else:
        diff_text = patch_path.read_text(encoding="utf-8")

    # 2. Apply the patch
    try:
        logger.info(f"Applying patch for case {case_id} to {REPO_ROOT}")
        # Use git apply to apply the unified diff
        process = subprocess.run(
            ["git", "apply", "-"],
            input=diff_text,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if process.returncode != 0:
            error_msg = process.stderr or "Unknown git apply error"
            logger.error(f"Patch application failed for {case_id}: {error_msg}")
            return {
                "status": "failed",
                "error": error_msg,
                "detail": "Git was unable to apply this patch. It might be stale or conflict with current code."
            }

        # 3. Log the decision in Lineage
        async with AsyncSessionLocal() as db:
            decision = DecisionLineage(
                decision_type="UI_REPAIR_PATCH_APPLIED",
                component_name="RepairLab",
                summary=f"Operator applied autonomous repair patch for {case_id}",
                rationale="Human-in-the-loop approval granted via Control Plane Dashboard.",
                outcome="SUCCESS",
                trigger_event={"case_id": case_id},
                meta_data={"case_id": case_id, "applied_at": datetime.now(UTC).isoformat()}
            )
            db.add(decision)

            # Update the review status if found
            q = select(UIRepairPRReview).where(UIRepairPRReview.case_id == case_id).order_by(desc(UIRepairPRReview.created_at))
            res = await db.execute(q)
            review = res.scalars().first()
            if review:
                review.status = "APPLIED"
                review.governance_decision = "APPROVED_BY_OPERATOR"

            await db.commit()

        logger.info(f"Successfully applied patch for case {case_id}")
        return {"status": "ok", "message": "Patch applied successfully and recorded in lineage."}

    except Exception as e:
        logger.exception(f"Exception during patch application for {case_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System error while applying patch: {str(e)}"
        )

@router.get("/cases/{case_id}/patch")
async def get_case_patch(case_id: str):
    """Returns the generated patch diff for a given case."""
    patch_path = REPAIR_OUTPUTS_DIR / case_id / "patch.diff"
    if not patch_path.exists():
        raise HTTPException(status_code=404, detail="Patch not found")

    return {"case_id": case_id, "diff": patch_path.read_text(encoding="utf-8")}
