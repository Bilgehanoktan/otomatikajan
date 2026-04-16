
"""
services/workflow_api/repair_lab_router.py — Phase 28
Exposes Laboratory, Tournament, and Tuning data to the Refine Dashboard.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc

from libs.db.session import AsyncSessionLocal
from libs.db.models.repair_models import (
    RepairBenchmarkRun,
    RepairTournament,
    RepairCandidate,
    VerifierResult,
    RepairMemory,
    RepairPattern,
    SelfTuningSuggestion
)

router = APIRouter(prefix="/api/v1/repair-lab", tags=["Autonomous Repair Lab"])

# ── Response Schemas ──────────────────────────────────────────────────────────

class CandidateSummary(BaseModel):
    strategy: str
    score: float
    status: str
    type: str

class TournamentOut(BaseModel):
    id: str
    incident_id: str
    winner_id: Optional[str]
    winner_score: float
    total_candidates: int
    created_at: datetime
    candidates: List[CandidateSummary] = []

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

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/benchmarks")
async def list_benchmarks(limit: int = 10):
    """Sistem performans benchmark geçmişini listeler."""
    async with AsyncSessionLocal() as db:
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

@router.get("/tournaments", response_model=List[TournamentOut])
async def list_tournaments(limit: int = 20):
    """Gerçekleşen tamir turnuvalarını ve aday skorlarını listeler."""
    async with AsyncSessionLocal() as db:
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
                        type=c.candidate_type or "code"
                    )
                    for c in candidates
                ]
            ))
        return results

@router.get("/verifiers/matrix")
async def get_verifier_matrix(tournament_id: Optional[str] = None):
    """Verifier Mesh performans matrisini döner."""
    async with AsyncSessionLocal() as db:
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

@router.get("/tuning/suggestions", response_model=List[TuningSuggestionOut])
async def get_tuning_suggestions():
    """Önerilen sistem ayar kalibrasyonlarını listeler."""
    async with AsyncSessionLocal() as db:
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

@router.get("/memory/heatmaps")
async def get_repair_memory():
    """Tamir hafızasındaki başarı/başarısızlık yoğunluk haritasını döner."""
    async with AsyncSessionLocal() as db:
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
