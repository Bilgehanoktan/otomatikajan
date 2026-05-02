
"""
services/improve/repair_bench.py — Phase 28
Orchestrates the Autonomous Repair Lab benchmarking and tournament execution.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from services.improve.benchmark_loader import RepairBenchLoader, BenchmarkCase
from services.observability.logging import get_logger
from libs.db.session import session_scope
from libs.llm.model_orchestrator import ModelOrchestrator
from libs.db.models.repair_models import RepairBenchmarkRun, RepairTournament, RepairCandidate, VerifierResult

logger = get_logger("repair.bench")

class BenchResult(BaseModel):
    case_id: str
    timestamp: datetime
    candidates_count: int
    best_candidate_id: Optional[str]
    success: bool
    score: float
    verification_summary: Dict[str, Any]
    learning_delta: Dict[str, Any]

class RepairBenchService:
    def __init__(self, model_orch: ModelOrchestrator, loader: Optional[RepairBenchLoader] = None):
        self.model_orch = model_orch
        self.loader = loader or RepairBenchLoader()
        self.results_history: List[BenchResult] = []

    async def run_benchmark_case(self, case_id: str, run_id: Optional[str] = None) -> Optional[BenchResult]:
        """Runs a single repair benchmark and evaluates the candidate tournament."""
        case = self.loader.load_case(case_id)
        if not case:
            return None

        from services.improve.patch_tournament import PatchTournament
        tournament = PatchTournament(model_orch=self.model_orch)
        tournament_res = await tournament.run_tournament(case)
        
        winner_eval = next((e for e in tournament_res.evaluations if e.candidate_id == tournament_res.winner_id), None)
        score = winner_eval.scores.total_score if winner_eval else 0.0
        success = score > 0.7 
        
        # --- MEMORY RECORDING ---
        from services.improve.repair_memory import RepairMemory, RepairMemoryEntry
        memory = RepairMemory()
        
        for cand_eval in tournament_res.evaluations:
            memory_entry = RepairMemoryEntry(
                case_id=case.id,
                incident_type=case.incident_id,
                subsystem=case.module,
                patch_strategy=next((c.strategy for c in tournament_res.candidates if c.id == cand_eval.candidate_id), "unknown"),
                outcome="success" if cand_eval.is_qualified and cand_eval.scores.total_score > 0.8 else "failure",
                score=cand_eval.scores.total_score,
                verifier_rejections=[k for k,v in cand_eval.scores.breakdown.items() if v < 0.5]
            )
            memory.record_outcome(memory_entry)

        result = BenchResult(
            case_id=case_id,
            timestamp=datetime.now(timezone.utc),
            candidates_count=len(tournament_res.candidates),
            best_candidate_id=tournament_res.winner_id,
            success=success,
            score=score,
            verification_summary={
                "rationale": tournament_res.winning_rationale,
                "evaluations_count": len(tournament_res.evaluations)
            },
            learning_delta={
                "tournament_id": tournament_res.tournament_id,
                "qualified_ratio": sum(1 for e in tournament_res.evaluations if e.is_qualified) / len(tournament_res.candidates) if tournament_res.candidates else 0
            }
        )
        
        # --- PERSISTENCE ---
        async with session_scope() as session:
            db_tourney = RepairTournament(
                tournament_id=tournament_res.tournament_id,
                run_id=run_id,
                incident_id=case.incident_id,
                project_id="sovereign-agi",
                cluster_id="local-lab",
                winner_candidate_id=tournament_res.winner_id,
                winner_score=score,
                verifier_score_breakdown=winner_eval.scores.breakdown if winner_eval else {},
                total_candidates=len(tournament_res.candidates)
            )
            session.add(db_tourney)
            
            for cand in tournament_res.candidates:
                db_cand = RepairCandidate(
                    candidate_id=cand.id,
                    tournament_id=tournament_res.tournament_id,
                    candidate_type=cand.type,
                    strategy=cand.strategy,
                    patch_diff=cand.content,
                    patch_signature=f"{case.module}:{cand.strategy}",
                    risk_score=0.0, # Will be filled by ranker in real flow
                    status="evaluated"
                )
                session.add(db_cand)
            
        self.results_history.append(result)
        return result

    async def run_full_bench(self) -> str:
        """Runs all cases in the index and returns a run_id."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        cases = self.loader.list_all_cases()
        
        async with session_scope() as session:
            db_run = RepairBenchmarkRun(
                run_id=run_id,
                project_id="sovereign-agi",
                cluster_id="local-lab",
                total_cases=len(cases),
                status="running"
            )
            session.add(db_run)
            
        for case in cases:
            await self.run_benchmark_case(case.id, run_id=run_id)
            
        # Update run stats
        stats = await self.get_lab_stats()
        async with session_scope() as session:
            from sqlalchemy import select
            q = select(RepairBenchmarkRun).where(RepairBenchmarkRun.run_id == run_id)
            db_run = (await session.execute(q)).scalar_one()
            db_run.success_rate = stats["success_rate"]
            db_run.avg_score = stats["avg_score"]
            db_run.end_time = datetime.now(timezone.utc)
            db_run.status = "completed"
            
        # Trigger Self-Tuning
        from services.improve.self_tuning_engine import SelfTuningEngine
        tuner = SelfTuningEngine(self)
        await tuner.generate_and_persist_recommendations()
            
        return run_id

    async def get_lab_stats(self) -> Dict[str, Any]:
        """Aggregated stats for the Phase 28 UI / report."""
        if not self.results_history:
            return {"status": "no_data"}
            
        success_rate = sum(1 for r in self.results_history if r.success) / len(self.results_history)
        avg_score = sum(r.score for r in self.results_history) / len(self.results_history)
        
        return {
            "total_runs": len(self.results_history),
            "success_rate": success_rate,
            "avg_score": avg_score,
            "top_failed_cases": [r.case_id for r in self.results_history if not r.success]
        }
