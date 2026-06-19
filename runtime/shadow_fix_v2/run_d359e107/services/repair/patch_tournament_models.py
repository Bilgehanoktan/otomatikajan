from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PatchTournamentWeights(BaseModel):
    test_score: float = 0.20
    build_score: float = 0.10
    risk_score: float = 0.15
    security_score: float = 0.15
    maintainability_score: float = 0.10
    rollback_safety_score: float = 0.10
    cognitive_integrity_score: float = 0.10
    historical_success_score: float = 0.05
    cost_score: float = 0.03
    blast_radius_score: float = 0.02

class ScoreBreakdown(BaseModel):
    test_score: float = 0.50
    build_score: float = 0.50
    risk_score: float = 0.50
    security_score: float = 0.50
    maintainability_score: float = 0.50
    rollback_safety_score: float = 0.50
    cognitive_integrity_score: float = 0.50
    historical_success_score: float = 0.50
    cost_score: float = 0.50
    blast_radius_score: float = 0.50

class ScoredCandidate(BaseModel):
    candidate_id: str
    eligible: bool = True
    final_score: float = 0.0
    rank: int = 1
    disqualification_reasons: List[str] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)

class PatchTournamentResult(BaseModel):
    incident_id: str
    run_id: str
    status: str = "completed"
    selected_candidate_id: Optional[str] = None
    requires_human_gate: bool = True
    scoring_weights: PatchTournamentWeights = Field(default_factory=PatchTournamentWeights)
    candidates: List[ScoredCandidate] = Field(default_factory=list)
    artifact_refs: Dict[str, str] = Field(default_factory=dict)
    created_at: str
