from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from services.project_factory.artifacts import _resolve_project_dir, load_project_factory_artifacts, write_project_factory_artifacts
from services.project_factory.models import CandidateReview
from services.project_factory.quality_scorecard import evaluate_quality_scorecard
from services.project_factory.risk_assessor import assess_project_risk

def run_candidate_review(
    project_id: str,
    workspace_root: Optional[str] = None
) -> CandidateReview:
    """
    Coordinates quality scorecard and risk assessment metrics.
    Aggregates reviews and saves candidate_review.json, transitioning project to CANDIDATE_REVIEWED.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    manifest_path = project_dir / "candidate_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"No candidate package manifest found for project {project_id}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # 1. Run evaluation sub-pipelines
    scorecard = evaluate_quality_scorecard(project_id, workspace_root)
    risk_assessment = assess_project_risk(project_id, workspace_root)

    # 2. Build CandidateReview model
    candidate_id = manifest_data.get("candidate_id", f"CAND-{project_id}")
    files_reviewed = [f.get("path") for f in manifest_data.get("files", [])]
    
    # Recommended decision logic
    recommended = "APPROVE_DELIVERY"
    if risk_assessment.risk_score >= 70 or len(risk_assessment.blocking_risks) > 0:
        recommended = "REJECT"
    elif risk_assessment.risk_score >= 40:
        recommended = "REQUEST_REVISION"

    review = CandidateReview(
        project_id=project_id,
        candidate_id=candidate_id,
        status="CANDIDATE_REVIEWED",
        summary="Sandbox candidate generated from approved scope.",
        files_reviewed=files_reviewed,
        quality_score=scorecard.score,
        risk_score=risk_assessment.risk_score,
        security_findings=risk_assessment.warnings,
        test_summary=manifest_data.get("tests", {"status": "UNKNOWN", "commands": []}),
        known_limitations=manifest_data.get("known_limitations", []),
        recommended_decision=recommended
    )

    # Save to disk
    review_path = project_dir / "candidate_review.json"
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(review.model_dump(), f, indent=2, ensure_ascii=False)

    # 3. Update brief and requirement gate status
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    brief.status = "CANDIDATE_REVIEWED"
    gate.status = "CANDIDATE_REVIEWED"
    write_project_factory_artifacts(brief, gate, workspace_root)

    return review

def load_candidate_review(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Loads candidate_review.json if it exists.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    review_path = project_dir / "candidate_review.json"
    if not review_path.exists():
        return None
    with open(review_path, "r", encoding="utf-8") as f:
        return json.load(f)
