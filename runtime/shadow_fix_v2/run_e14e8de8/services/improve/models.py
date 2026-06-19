
"""
services/improve/models.py — Phase 28
Data models for the Repair Lab Tournament.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RepairCandidate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "patch", "policy", "config"
    content: str
    strategy: str  # "conservative", "radical", "minimal", "performant"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = {}

class CandidateScore(BaseModel):
    syntax_score: float = 0.0
    regression_score: float = 0.0
    policy_score: float = 0.0
    risk_score: float = 0.0
    economic_score: float = 0.0
    similarity_score: float = 0.0
    total_score: float = 0.0
    breakdown: Dict[str, Any] = {} # Per-verifier details
    justification: str = ""

class CandidateEvaluation(BaseModel):
    candidate_id: str
    scores: CandidateScore
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_qualified: bool = True

class TournamentResult(BaseModel):
    tournament_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    candidates: List[RepairCandidate]
    evaluations: List[CandidateEvaluation]
    winner_id: Optional[str]
    winning_rationale: str = ""
    started_at: datetime
    completed_at: datetime

class RepairMemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    incident_type: str
    subsystem: str
    patch_strategy: str
    outcome: str # "success", "failure", "rollback"
    failure_reason: Optional[str] = None
    verifier_rejections: List[str] = []
    score: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: Dict[str, Any] = {}

class PatchPattern(BaseModel):
    pattern_id: str
    subsystem: str
    avg_success_rate: float
    total_attempts: int
    recommendation: str # "boost", "penalize", "stable"
