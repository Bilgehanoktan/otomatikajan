import pytest
import uuid
from datetime import datetime, timezone
from libs.db.models.repair_models import UIRepairPRReview, UIRepairPRFinding
from services.repair.repair_models import (
    UIRepairPRReview as UIRepairPRReviewDC,
    UIRepairPRFinding as UIRepairPRFindingDC
)

def test_ui_repair_db_models():
    """Verify SQLAlchemy models for UI Repair PR Review & Findings."""
    review_id = str(uuid.uuid4())
    case_id = "job-123"
    pr_url = "https://github.com/org/repo/pull/1"
    
    review = UIRepairPRReview(
        review_id=review_id,
        case_id=case_id,
        pr_url=pr_url,
        status="PENDING",
        summary="Test review summary",
        confidence_score=0.85,
        verifier_mesh_pass=True,
        governance_decision="PENDING"
    )
    
    assert review.review_id == review_id
    assert review.case_id == case_id
    assert review.pr_url == pr_url
    assert review.status == "PENDING"
    assert review.confidence_score == 0.85
    assert review.verifier_mesh_pass is True

    finding_id = str(uuid.uuid4())
    finding = UIRepairPRFinding(
        finding_id=finding_id,
        review_id=review_id,
        severity="error",
        category="security",
        message="Unsafe input handling",
        file_path="apps/refine_control_plane/src/app/page.tsx",
        line_number=42,
        suggestion="Use sanitized input"
    )
    
    assert finding.finding_id == finding_id
    assert finding.review_id == review_id
    assert finding.severity == "error"
    assert finding.message == "Unsafe input handling"


def test_ui_repair_dataclasses():
    """Verify dataclass models for UI Repair PR Review & Findings."""
    review_id = "rev-456"
    case_id = "job-456"
    
    finding = UIRepairPRFindingDC(
        finding_id="find-789",
        review_id=review_id,
        severity="warning",
        category="quality",
        message="Large component",
        suggestion="Split into smaller components"
    )
    
    review = UIRepairPRReviewDC(
        review_id=review_id,
        case_id=case_id,
        pr_url="https://github.com/org/repo/pull/2",
        status="RUNNING",
        findings=[finding]
    )
    
    assert review.review_id == review_id
    assert len(review.findings) == 1
    assert review.findings[0].finding_id == "find-789"
