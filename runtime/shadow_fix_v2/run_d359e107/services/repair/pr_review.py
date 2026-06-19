from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PRAgentReviewArtifact(BaseModel):
    incident_id: str
    run_id: str
    review_source: str = "pr_agent"
    agent_key: str = "pr_agent"
    requested_mode: str = "review_gate"
    status: str = "completed"
    summary: str
    possible_bugs: List[str] = Field(default_factory=list)
    security_findings: List[str] = Field(default_factory=list)
    suggested_improvements: List[str] = Field(default_factory=list)
    blocking_comments: List[str] = Field(default_factory=list)
    review_effort: str = "medium"
    confidence_score: float = 0.82
    artifact_refs: Dict[str, str] = Field(default_factory=dict)

def build_pr_review_artifact(
    incident_id: str,
    run_id: str,
    summary: str,
    possible_bugs: List[str],
    security_findings: List[str],
    suggested_improvements: List[str],
    blocking_comments: List[str],
    confidence_score: float = 0.82,
    artifact_refs: Optional[Dict[str, str]] = None,
) -> PRAgentReviewArtifact:
    """
    Builds a PRAgentReviewArtifact instance.
    """
    refs = artifact_refs or {}
    return PRAgentReviewArtifact(
        incident_id=incident_id,
        run_id=run_id,
        summary=summary,
        possible_bugs=possible_bugs,
        security_findings=security_findings,
        suggested_improvements=suggested_improvements,
        blocking_comments=blocking_comments,
        confidence_score=confidence_score,
        artifact_refs=refs
    )

def validate_pr_review_artifact(data: Dict[str, Any]) -> PRAgentReviewArtifact:
    """
    Validates a dictionary against the PRAgentReviewArtifact schema.
    """
    return PRAgentReviewArtifact(**data)
