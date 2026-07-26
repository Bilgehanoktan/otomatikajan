import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from bilgeapi.services.pr_draft import PatchRiskAnalyzer, PrDraftService, PrDraftBodyBuilder
from bilgeapi.services.audit import AuditService
from bilgeapi.repositories.memory import InMemoryPrDraftRepository, InMemoryImprovementRepository, InMemoryAuditRepository
from bilgeapi.adapters.github_pr import MockGitHubPrAdapter, GitHubDraftPrAdapter


def test_patch_risk_analyzer():
    analyzer = PatchRiskAnalyzer()

    # Case 1: Touch sensitive auth.py file -> HIGH risk
    high_patch = (
        "diff --git a/apps/bilgeapi/auth.py b/apps/bilgeapi/auth.py\n"
        "--- a/apps/bilgeapi/auth.py\n"
        "+++ b/apps/bilgeapi/auth.py\n"
        "@@ -10,2 +10,3 @@\n"
        " def check_auth():\n"
        "+    # Security tweak\n"
        "     pass\n"
    )
    analysis_high = analyzer.analyze_risk(high_patch)
    assert analysis_high["risk_level"] == "HIGH"
    assert "apps/bilgeapi/auth.py" in analysis_high["risk_flags"]
    assert "apps/bilgeapi/auth.py" in analysis_high["affected_files"]

    # Case 2: Touch regular main.py file -> LOW risk
    low_patch = (
        "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
        "--- a/apps/bilgeapi/main.py\n"
        "+++ b/apps/bilgeapi/main.py\n"
        "@@ -20,2 +20,3 @@\n"
        " def index():\n"
        "+    # Regular comment\n"
        "     return {}\n"
    )
    analysis_low = analyzer.analyze_risk(low_patch)
    assert analysis_low["risk_level"] == "LOW"
    assert len(analysis_low["risk_flags"]) == 0
    assert "apps/bilgeapi/main.py" in analysis_low["affected_files"]


@pytest.mark.asyncio
async def test_pr_draft_service_gates():
    pr_draft_repo = InMemoryPrDraftRepository()
    proposal_repo = InMemoryImprovementRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)
    adapter = MockGitHubPrAdapter()
    
    service = PrDraftService(pr_draft_repo, proposal_repo, adapter, audit_service)

    # 1. Proposal not found
    with pytest.raises(ValueError, match="Proposal not found"):
        await service.create_draft_pr("non_existent_proposal", "admin")

    # 2. Proposal not approved
    prop_unapproved = await proposal_repo.create_proposal({
        "research_id": "res_1",
        "title": "Fix Memory Leak",
        "rationale": "Memory leaks found in loop",
        "patch_code": "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py",
        "risk_analysis": {"confidence_level": "HIGH", "confidence_score": 90.0},
        "gate_status": "GATE_PASSED",
        "approval_status": "REVIEW_REQUIRED",
    })

    with pytest.raises(ValueError, match="Proposal is not approved"):
        await service.create_draft_pr(prop_unapproved["id"], "admin")

    # Verify audit event for unapproved block
    events_unappr = await audit_repo.list_recent()
    assert any(e.event_type == "PR_DRAFT_BLOCKED_UNAPPROVED" and e.entity_id == prop_unapproved["id"] for e in events_unappr)

    # 3. Proposal approved but gate has not passed (e.g. GATE_FAILED or DRAFT)
    prop_gate_failed = await proposal_repo.create_proposal({
        "research_id": "res_2",
        "title": "Fix Input Validation",
        "rationale": "Unvalidated parameters",
        "patch_code": "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py",
        "risk_analysis": {"confidence_level": "HIGH", "confidence_score": 90.0},
        "gate_status": "GATE_FAILED",
        "approval_status": "APPROVED",
    })

    with pytest.raises(ValueError, match="Proposal has not passed release gate simulation"):
        await service.create_draft_pr(prop_gate_failed["id"], "admin")

    events_gate = await audit_repo.list_recent()
    assert any(e.event_type == "PR_DRAFT_BLOCKED_GATE_FAILED" and e.entity_id == prop_gate_failed["id"] for e in events_gate)

    # 4. Proposal approved, gate passed, but confidence level is LOW
    prop_low_conf = await proposal_repo.create_proposal({
        "research_id": "res_3",
        "title": "Tweak config file",
        "rationale": "low trust sources",
        "patch_code": "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py",
        "risk_analysis": {"confidence_level": "LOW", "confidence_score": 45.0},
        "gate_status": "GATE_PASSED",
        "approval_status": "APPROVED",
    })

    with pytest.raises(ValueError, match="Low confidence proposals cannot generate PR drafts"):
        await service.create_draft_pr(prop_low_conf["id"], "admin")

    events_conf = await audit_repo.list_recent()
    assert any(e.event_type == "PR_DRAFT_BLOCKED_LOW_CONFIDENCE" and e.entity_id == prop_low_conf["id"] for e in events_conf)


@pytest.mark.asyncio
async def test_pr_draft_creation_success():
    pr_draft_repo = InMemoryPrDraftRepository()
    proposal_repo = InMemoryImprovementRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)
    adapter = MockGitHubPrAdapter()

    service = PrDraftService(pr_draft_repo, proposal_repo, adapter, audit_service)

    # Create valid approved + gate_passed + high confidence proposal
    prop = await proposal_repo.create_proposal({
        "research_id": "res_success",
        "title": "Optimize DB connections",
        "rationale": "High connection count fixes",
        "patch_code": (
            "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
            "--- a/apps/bilgeapi/main.py\n"
            "+++ b/apps/bilgeapi/main.py\n"
        ),
        "risk_analysis": {"confidence_level": "HIGH", "confidence_score": 95.0},
        "gate_status": "GATE_PASSED",
        "approval_status": "APPROVED",
    })

    result = await service.create_draft_pr(prop["id"], "admin_user_1")

    assert result["status"] == "COMPLETED"
    assert "mock-owner" in result["github_pr_url"]
    assert result["risk_level"] == "LOW"
    assert result["created_by"] == "admin_user_1"
    
    # Body validation
    assert "Problem Özeti" in result["body"]
    assert "Rationale & Evidence Chain" in result["body"]
    assert "Rollback Planı" in result["body"]
    assert "Human Review Checklist" in result["body"]

    # Verify audit events
    events = await audit_repo.list_recent()
    assert any(e.event_type == "PR_DRAFT_REQUESTED" and e.entity_id == prop["id"] for e in events)
    assert any(e.event_type == "PR_DRAFT_CREATED" and e.entity_id == prop["id"] for e in events)


def test_pr_draft_body_high_risk_warning():
    body = PrDraftBodyBuilder.build_body(
        title="Tweak DB credentials",
        rationale="Optimize config settings",
        patch_code="diff --git a/apps/bilgeapi/config.py b/apps/bilgeapi/config.py",
        affected_files=["apps/bilgeapi/config.py"],
        risk_level="HIGH",
        risk_flags=["apps/bilgeapi/config.py"],
        confidence_score=90.0,
        confidence_level="HIGH"
    )

    assert "High Risk Review Required" in body
    assert "WARNING" in body
    assert "`apps/bilgeapi/config.py`" in body


def test_improvements_pr_draft_endpoints(test_client):
    from bilgeapi.repositories.memory import memory_repositories

    # Seed mock data in-memory
    prop_id = "prp_test_endpoint"
    memory_repositories.improvement_proposals[prop_id] = {
        "id": prop_id,
        "research_id": "res_123",
        "title": "Endpoint optimize test",
        "rationale": "High-level improvements",
        "patch_code": "diff --git deadline/apps/bilgeapi/main.py b/apps/bilgeapi/main.py",
        "risk_analysis": {"confidence_level": "HIGH", "confidence_score": 92.0},
        "gate_status": "GATE_PASSED",
        "approval_status": "APPROVED",
        "approved_by": "admin",
        "approved_at": datetime.now(timezone.utc),
        "ready_for_human_apply": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    # 1. Trigger draft PR creation
    resp = test_client.post(f"/v1/improvements/proposals/{prop_id}/draft-pr/create")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert "mock-owner" in data["github_pr_url"]
    assert data["risk_level"] == "LOW"

    # 2. Get list of draft PRs for this proposal
    resp_list = test_client.get(f"/v1/improvements/proposals/{prop_id}/draft-prs")
    assert resp_list.status_code == 200
    prs = resp_list.json()
    assert len(prs) == 1
    assert prs[0]["id"] == data["id"]


@pytest.mark.asyncio
async def test_github_draft_pr_adapter():
    adapter = GitHubDraftPrAdapter(
        token="test-token",
        owner="test-owner",
        repo="test-repo",
        base_branch="main",
        allow_real=True
    )

    mock_response_ref = MagicMock()
    mock_response_ref.status_code = 200
    mock_response_ref.json.return_value = {"object": {"sha": "base_commit_sha"}}

    mock_response_ref_create = MagicMock()
    mock_response_ref_create.status_code = 201

    mock_response_content_get = MagicMock()
    mock_response_content_get.status_code = 404

    mock_response_content_put = MagicMock()
    mock_response_content_put.status_code = 201

    mock_response_pr = MagicMock()
    mock_response_pr.status_code = 201
    mock_response_pr.json.return_value = {"html_url": "https://github.com/test-owner/test-repo/pull/42"}

    with patch("httpx.AsyncClient.get") as mock_get, \
         patch("httpx.AsyncClient.post") as mock_post, \
         patch("httpx.AsyncClient.put") as mock_put:
        
        mock_get.side_effect = [mock_response_ref, mock_response_content_get]
        mock_post.side_effect = [mock_response_ref_create, mock_response_pr]
        mock_put.return_value = mock_response_content_put

        url = await adapter.create_draft_pr(
            title="Optimized query",
            body="Review fixes",
            branch_name="bilgeapi-patch-123",
            patch_code="diff --git ...",
            affected_files=["apps/bilgeapi/main.py"]
        )

        assert url == "https://github.com/test-owner/test-repo/pull/42"


@pytest.mark.asyncio
async def test_github_draft_pr_adapter_disabled():
    adapter = GitHubDraftPrAdapter(
        token="test-token",
        owner="test-owner",
        repo="test-repo",
        base_branch="main",
        allow_real=False
    )
    url = await adapter.create_draft_pr(
        title="Optimized query",
        body="Review fixes",
        branch_name="bilgeapi-patch-123",
        patch_code="diff --git ...",
        affected_files=["apps/bilgeapi/main.py"]
    )
    assert "pull/mock" in url


@pytest.mark.asyncio
async def test_pr_draft_service_exception_handling():
    pr_draft_repo = InMemoryPrDraftRepository()
    proposal_repo = InMemoryImprovementRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)
    
    adapter = MagicMock()
    adapter.create_draft_pr.side_effect = Exception("GitHub API failure")

    service = PrDraftService(pr_draft_repo, proposal_repo, adapter, audit_service)

    prop = await proposal_repo.create_proposal({
        "research_id": "res_fail_db",
        "title": "Fix something",
        "rationale": "High-level improvements",
        "patch_code": "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py",
        "risk_analysis": {"confidence_level": "HIGH", "confidence_score": 90.0},
        "gate_status": "GATE_PASSED",
        "approval_status": "APPROVED",
    })

    with pytest.raises(Exception, match="GitHub API failure"):
        await service.create_draft_pr(prop["id"], "admin")

    events = await audit_repo.list_recent()
    assert any(e.event_type == "PR_DRAFT_FAILED" and e.entity_id == prop["id"] for e in events)

