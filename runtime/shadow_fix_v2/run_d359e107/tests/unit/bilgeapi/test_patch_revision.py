import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from apps.bilgeapi.services.patch_revision import ReviewerFeedbackService, PatchRevisionEngine
from apps.bilgeapi.services.pr_verification import PrVerificationService
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.repositories.memory import (
    InMemoryPrVerificationRepository,
    InMemoryPrDraftRepository,
    InMemoryImprovementRepository,
    InMemoryResearchRepository,
    InMemoryAuditRepository,
    InMemoryPrReviewFeedbackRepository,
    InMemoryPatchRevisionRepository
)


@pytest.mark.asyncio
async def test_reviewer_feedback_service_transitions():
    feedback_repo = InMemoryPrReviewFeedbackRepository()
    pr_draft_repo = InMemoryPrDraftRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)

    service = ReviewerFeedbackService(feedback_repo, pr_draft_repo, audit_service)

    # 1. PR Draft not found error
    with pytest.raises(ValueError, match="PR Draft not found"):
        await service.add_feedback("invalid_pr", "Looks bad", "reviewer_1", "actor_1")

    # Create a dummy PR Draft
    draft = await pr_draft_repo.create_pr_draft({
        "proposal_id": "prop_123",
        "provider": "github",
        "title": "Initial Draft",
        "body": "Initial Body",
        "risk_level": "LOW"
    })

    # Add feedback successfully
    fb = await service.add_feedback(draft["id"], "Please change variable name", "reviewer_1", "actor_1")
    assert fb["pr_draft_id"] == draft["id"]
    assert fb["comment"] == "Please change variable name"
    assert fb["status"] == "PENDING"

    # Verify audit event logged
    events = await audit_repo.list_recent()
    assert any(e.event_type == "PR_REVIEW_FEEDBACK_ADDED" for e in events)

    # Get feedback
    fb_fetched = await service.get_feedback(fb["id"])
    assert fb_fetched["id"] == fb["id"]

    # List feedback
    fbs = await service.list_feedback_by_pr_draft(draft["id"])
    assert len(fbs) == 1
    assert fbs[0]["id"] == fb["id"]

    # Transition PENDING -> RESOLVED (Valid)
    fb_updated = await service.update_feedback_status(fb["id"], "RESOLVED", "actor_1")
    assert fb_updated["status"] == "RESOLVED"

    # Transition from closed status -> PENDING (Invalid)
    with pytest.raises(ValueError, match="Cannot transition from closed status 'RESOLVED' to 'PENDING'"):
        await service.update_feedback_status(fb["id"], "PENDING", "actor_1")

    # Transition from closed status -> SUPERSEDED (Invalid)
    with pytest.raises(ValueError, match="Cannot transition from closed status 'RESOLVED' to 'SUPERSEDED'"):
        await service.update_feedback_status(fb["id"], "SUPERSEDED", "actor_1")

    # Check PENDING -> SUPERSEDED (Valid)
    fb2 = await service.add_feedback(draft["id"], "Another comment", "reviewer_1", "actor_1")
    fb2_updated = await service.update_feedback_status(fb2["id"], "SUPERSEDED", "actor_1")
    assert fb2_updated["status"] == "SUPERSEDED"


@pytest.mark.asyncio
async def test_patch_revision_engine():
    revision_repo = InMemoryPatchRevisionRepository()
    pr_draft_repo = InMemoryPrDraftRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)

    engine = PatchRevisionEngine(revision_repo, pr_draft_repo, audit_service)

    # Create dummy PR Draft
    draft = await pr_draft_repo.create_pr_draft({
        "proposal_id": "prop_123",
        "provider": "github",
        "title": "Initial Draft",
        "body": "Initial Body",
        "risk_level": "LOW"
    })

    # Create revision 1 (Low risk patch)
    patch_1 = (
        "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
        "--- a/apps/bilgeapi/main.py\n"
        "+++ b/apps/bilgeapi/main.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+# clean fix\n"
    )
    rev1 = await engine.create_revision(draft["id"], None, patch_1, "admin")
    assert rev1["revision_number"] == 1
    assert rev1["risk_level"] == "LOW"
    assert rev1["verification_status"] == "PENDING"

    # Create revision 2 (High risk patch - touches config.py)
    patch_2 = (
        "diff --git a/apps/bilgeapi/config.py b/apps/bilgeapi/config.py\n"
        "--- a/apps/bilgeapi/config.py\n"
        "+++ b/apps/bilgeapi/config.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+# changing security settings\n"
    )
    rev2 = await engine.create_revision(draft["id"], None, patch_2, "admin")
    assert rev2["revision_number"] == 2
    assert rev2["risk_level"] == "HIGH"  # config.py is risky

    # Create revision 3 (Medium risk patch - size > 100 or affected files > 3)
    patch_3 = (
        "diff --git a/apps/bilgeapi/f1.py b/apps/bilgeapi/f1.py\n"
        "+++ b/apps/bilgeapi/f1.py\n"
        "diff --git a/apps/bilgeapi/f2.py b/apps/bilgeapi/f2.py\n"
        "+++ b/apps/bilgeapi/f2.py\n"
        "diff --git a/apps/bilgeapi/f3.py b/apps/bilgeapi/f3.py\n"
        "+++ b/apps/bilgeapi/f3.py\n"
        "diff --git a/apps/bilgeapi/f4.py b/apps/bilgeapi/f4.py\n"
        "+++ b/apps/bilgeapi/f4.py\n"
    )
    rev3 = await engine.create_revision(draft["id"], None, patch_3, "admin")
    assert rev3["revision_number"] == 3
    assert rev3["risk_level"] == "MEDIUM"

    # Fetch revisions
    rev_fetched = await engine.get_revision(rev1["id"])
    assert rev_fetched["id"] == rev1["id"]

    revs = await engine.list_revisions_by_pr_draft(draft["id"])
    assert len(revs) == 3
    assert revs[0]["revision_number"] == 3  # Sorted desc


@pytest.mark.asyncio
async def test_revision_verification_service():
    verification_repo = InMemoryPrVerificationRepository()
    pr_draft_repo = InMemoryPrDraftRepository()
    proposal_repo = InMemoryImprovementRepository()
    research_repo = InMemoryResearchRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)
    revision_repo = InMemoryPatchRevisionRepository()

    service = PrVerificationService(
        verification_repo=verification_repo,
        pr_draft_repo=pr_draft_repo,
        proposal_repo=proposal_repo,
        research_repo=research_repo,
        audit_service=audit_service,
        revision_repo=revision_repo
    )

    # 1. Invalid revision ID
    with pytest.raises(ValueError, match="Patch Revision not found"):
        await service.verify_revision("invalid_revision", "admin")

    # Create dummy proposal
    proposal = await proposal_repo.create_proposal({
        "research_id": "res_123",
        "title": "Fix Memory",
        "rationale": "Memory leaks",
        "patch_code": "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py",
        "risk_analysis": {"confidence_level": "HIGH"},
        "gate_status": "GATE_PASSED",
        "approval_status": "APPROVED"
    })

    # Create dummy draft PR
    draft = await pr_draft_repo.create_pr_draft({
        "proposal_id": proposal["id"],
        "provider": "github",
        "title": "Fix bug",
        "body": "Fixes bug",
        "risk_level": "LOW"
    })

    # Add evidence
    await research_repo.create_evidence({
        "research_id": "res_123",
        "source_url": "https://google.com",
        "source_domain": "google.com",
        "content_hash": "hash123",
        "trust_score": 80.0
    })

    # Create a revision (Low risk)
    patch_clean = (
        "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
        "--- a/apps/bilgeapi/main.py\n"
        "+++ b/apps/bilgeapi/main.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+# clean fix\n"
    )
    rev_engine = PatchRevisionEngine(revision_repo, pr_draft_repo, audit_service)
    rev = await rev_engine.create_revision(draft["id"], None, patch_clean, "admin")

    # Verify revision
    verification = await service.verify_revision(rev["id"], "admin")
    assert verification["revision_id"] == rev["id"]
    assert verification["review_decision"] in ["REVIEW_READY", "NEEDS_HUMAN_CAUTION"]
    
    # Check that revision status is updated to VERIFIED
    rev_updated = await revision_repo.get_revision(rev["id"])
    assert rev_updated["verification_status"] == "VERIFIED"

    # Create a revision that will fail (high risk + no tests -> score < 70, or let's just make it fail)
    # Actually, we can check a failing case by providing low confidence or bad patch.
    # Score formula breakdown:
    # 1. Confidence level LOW: +0
    # 2. No evidence: +0
    # 3. No test: +0
    # 4. Risky file config.py: +0
    # 5. Rollback: +10
    # 6. Audit: +10
    # Total score: 20 -> Decision: BLOCKED
    proposal_bad = await proposal_repo.create_proposal({
        "research_id": None,
        "title": "Bad Proposal",
        "rationale": "bad",
        "patch_code": "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py",
        "risk_analysis": {"confidence_level": "LOW"},
        "gate_status": "GATE_PASSED",
        "approval_status": "APPROVED"
    })
    draft_bad = await pr_draft_repo.create_pr_draft({
        "proposal_id": proposal_bad["id"],
        "provider": "github",
        "title": "Bad Draft",
        "body": "Bad Body",
        "risk_level": "LOW"
    })
    
    patch_bad = (
        "diff --git a/apps/bilgeapi/config.py b/apps/bilgeapi/config.py\n"
        "--- a/apps/bilgeapi/config.py\n"
        "+++ b/apps/bilgeapi/config.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+# config change\n"
    )
    rev_bad = await rev_engine.create_revision(draft_bad["id"], None, patch_bad, "admin")
    
    verification_bad = await service.verify_revision(rev_bad["id"], "admin")
    assert verification_bad["review_decision"] == "BLOCKED"
    
    rev_bad_updated = await revision_repo.get_revision(rev_bad["id"])
    assert rev_bad_updated["verification_status"] == "FAILED"


@pytest.mark.asyncio
async def test_reviewer_feedback_and_revision_api_endpoints(monkeypatch, test_client_real_auth):
    from apps.bilgeapi.config import settings
    # Enable API Key Auth Mode with role mapping
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator"])

    from apps.bilgeapi.routers.deps import (
        get_pr_draft_repository,
        get_improvement_repository,
        get_pr_review_feedback_repository,
        get_patch_revision_repository,
        get_research_repository
    )
    
    app = test_client_real_auth.app
    pr_draft_repo = app.dependency_overrides[get_pr_draft_repository]()
    proposal_repo = app.dependency_overrides[get_improvement_repository]()
    feedback_repo = app.dependency_overrides[get_pr_review_feedback_repository]()
    revision_repo = app.dependency_overrides[get_patch_revision_repository]()
    research_repo = app.dependency_overrides[get_research_repository]()

    # Setup dummy data
    proposal = await proposal_repo.create_proposal({
        "research_id": "res_xyz",
        "title": "Optimizing API",
        "rationale": "fast",
        "patch_code": "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py",
        "risk_analysis": {"confidence_level": "HIGH"},
        "gate_status": "GATE_PASSED",
        "approval_status": "APPROVED"
    })
    draft = await pr_draft_repo.create_pr_draft({
        "proposal_id": proposal["id"],
        "provider": "github",
        "title": "API optimization",
        "body": "optimize",
        "risk_level": "LOW"
    })

    # Add evidence
    await research_repo.create_evidence({
        "research_id": "res_xyz",
        "source_url": "https://google.com",
        "source_domain": "google.com",
        "content_hash": "hash123",
        "trust_score": 80.0
    })

    op_headers = {"X-API-Key": "op_key"}
    admin_headers = {"X-API-Key": "admin_key"}

    # 1. Create feedback (POST /feedback) - accessible by operator
    fb_payload = {
        "comment": "Nice work but rename this function",
        "reviewer_id": "reviewer_xyz"
    }
    resp_fb = test_client_real_auth.post(
        f"/v1/improvements/pr-drafts/{draft['id']}/feedback",
        json=fb_payload,
        headers=op_headers
    )
    assert resp_fb.status_code == 201
    fb_data = resp_fb.json()
    assert fb_data["comment"] == "Nice work but rename this function"
    assert fb_data["status"] == "PENDING"

    # 2. List feedback (GET /feedback) - accessible by operator
    resp_list_fb = test_client_real_auth.get(
        f"/v1/improvements/pr-drafts/{draft['id']}/feedback",
        headers=op_headers
    )
    assert resp_list_fb.status_code == 200
    assert len(resp_list_fb.json()) == 1

    # 3. Create revision (POST /revisions) - admin only
    rev_payload = {
        "feedback_id": fb_data["id"],
        "revised_patch_code": (
            "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
            "--- a/apps/bilgeapi/main.py\n"
            "+++ b/apps/bilgeapi/main.py\n"
            "@@ -1,2 +1,3 @@\n"
            "+# updated comment\n"
        )
    }
    # Fail with operator key
    resp_rev_fail = test_client_real_auth.post(
        f"/v1/improvements/pr-drafts/{draft['id']}/revisions",
        json=rev_payload,
        headers=op_headers
    )
    assert resp_rev_fail.status_code == 403

    # Succeed with admin key
    resp_rev = test_client_real_auth.post(
        f"/v1/improvements/pr-drafts/{draft['id']}/revisions",
        json=rev_payload,
        headers=admin_headers
    )
    assert resp_rev.status_code == 201
    rev_data = resp_rev.json()
    assert rev_data["revision_number"] == 1
    assert rev_data["risk_level"] == "LOW"

    # 4. List revisions (GET /revisions) - accessible by operator
    resp_list_rev = test_client_real_auth.get(
        f"/v1/improvements/pr-drafts/{draft['id']}/revisions",
        headers=op_headers
    )
    assert resp_list_rev.status_code == 200
    assert len(resp_list_rev.json()) == 1

    # 5. Verify revision (POST /verify) - admin only
    # Fail with operator key
    resp_verify_fail = test_client_real_auth.post(
        f"/v1/improvements/revisions/{rev_data['id']}/verify",
        headers=op_headers
    )
    assert resp_verify_fail.status_code == 403

    # Succeed with admin key
    resp_verify = test_client_real_auth.post(
        f"/v1/improvements/revisions/{rev_data['id']}/verify",
        headers=admin_headers
    )
    assert resp_verify.status_code == 201
    verify_data = resp_verify.json()
    assert verify_data["revision_id"] == rev_data["id"]
    assert verify_data["status"] in ["REVIEW_READY", "NEEDS_HUMAN_CAUTION"]
