import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from bilgeapi.services.pr_verification import SandboxPatchAnalyzer, PrReviewGateScorer, PrVerificationService
from bilgeapi.services.audit import AuditService
from bilgeapi.repositories.memory import (
    InMemoryPrVerificationRepository,
    InMemoryPrDraftRepository,
    InMemoryImprovementRepository,
    InMemoryResearchRepository,
    InMemoryAuditRepository
)


def test_sandbox_patch_analyzer():
    analyzer = SandboxPatchAnalyzer()

    # Case 1: Touch sensitive file -> risky, high risk level
    sensitive_patch = (
        "diff --git a/apps/bilgeapi/auth.py b/apps/bilgeapi/auth.py\n"
        "--- a/apps/bilgeapi/auth.py\n"
        "+++ b/apps/bilgeapi/auth.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+# Some security change\n"
    )
    analysis_sensitive = analyzer.analyze_patch(sensitive_patch)
    assert "apps/bilgeapi/auth.py" in analysis_sensitive["affected_files"]
    assert "apps/bilgeapi/auth.py" in analysis_sensitive["risky_files"]
    assert analysis_sensitive["patch_size_lines"] == 1
    assert not analysis_sensitive["mutation_commands_detected"]

    # Case 2: Mutation command detected
    mutation_patch = (
        "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
        "--- a/apps/bilgeapi/main.py\n"
        "+++ b/apps/bilgeapi/main.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+import os\n"
        "+os.system('rm -rf /')\n"
    )
    analysis_mutation = analyzer.analyze_patch(mutation_patch)
    assert analysis_mutation["mutation_commands_detected"]

    # Case 3: Test files present
    test_patch = (
        "diff --git a/tests/unit/bilgeapi/test_some.py b/tests/unit/bilgeapi/test_some.py\n"
        "--- a/tests/unit/bilgeapi/test_some.py\n"
        "+++ b/tests/unit/bilgeapi/test_some.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+def test_hello(): pass\n"
    )
    analysis_test = analyzer.analyze_patch(test_patch)
    assert "tests/unit/bilgeapi/test_some.py" in analysis_test["test_files"]


def test_pr_review_gate_scorer():
    scorer = PrReviewGateScorer()

    # Low risk, high score -> REVIEW_READY
    # Evidence trust >= 50: +20
    # Confidence level HIGH/MEDIUM: +20
    # Test file present: +15
    # Risk-free (no risky files): +15
    # Patch size <= 50: +10
    # Rollback plan: +10
    # Audit trail: +10
    # Total: 100
    analysis = {
        "affected_files": ["apps/bilgeapi/main.py", "tests/unit/test_main.py"],
        "risky_files": [],
        "test_files": ["tests/unit/test_main.py"],
        "patch_size_lines": 20,
        "mutation_commands_detected": False
    }
    proposal = {
        "risk_analysis": {"confidence_level": "HIGH"}
    }
    evidences = [{"trust_score": 60.0}]

    res = scorer.calculate_score(analysis, proposal, evidences)
    assert res["score"] == 100.0
    assert res["review_decision"] == "REVIEW_READY"
    assert res["risk_level"] == "LOW"

    # High risk -> Downgraded to NEEDS_HUMAN_CAUTION even if score is 85+ (e.g. 90)
    analysis_high = {
        "affected_files": ["apps/bilgeapi/auth.py"],
        "risky_files": ["apps/bilgeapi/auth.py"],
        "test_files": [],
        "patch_size_lines": 5,
        "mutation_commands_detected": False
    }
    # Score details:
    # Confidence HIGH: +20
    # Evidence trust >= 50: +20
    # Test file: 0
    # Risk-free: 0
    # Patch size: +10
    # Rollback: +10
    # Audit: +10
    # Total: 70 -> Decision: NEEDS_HUMAN_CAUTION (score between 70 and 84)
    res_high = scorer.calculate_score(analysis_high, proposal, evidences)
    assert res_high["score"] == 70.0
    assert res_high["review_decision"] == "NEEDS_HUMAN_CAUTION"
    assert res_high["risk_level"] == "HIGH"

    # High risk with 85+ score (e.g. if we add test files and make it 85 score)
    analysis_high_test = {
        "affected_files": ["apps/bilgeapi/auth.py", "tests/unit/test_auth.py"],
        "risky_files": ["apps/bilgeapi/auth.py"],
        "test_files": ["tests/unit/test_auth.py"],
        "patch_size_lines": 5,
        "mutation_commands_detected": False
    }
    # Score details:
    # Confidence HIGH: +20
    # Evidence trust >= 50: +20
    # Test file: +15
    # Risk-free: 0
    # Patch size: +10
    # Rollback: +10
    # Audit: +10
    # Total: 85 -> Decision would be REVIEW_READY but since risk is HIGH, downgraded to NEEDS_HUMAN_CAUTION
    res_high_test = scorer.calculate_score(analysis_high_test, proposal, evidences)
    assert res_high_test["score"] == 85.0
    assert res_high_test["review_decision"] == "NEEDS_HUMAN_CAUTION"
    assert res_high_test["risk_level"] == "HIGH"


@pytest.mark.asyncio
async def test_pr_verification_service():
    verification_repo = InMemoryPrVerificationRepository()
    pr_draft_repo = InMemoryPrDraftRepository()
    proposal_repo = InMemoryImprovementRepository()
    research_repo = InMemoryResearchRepository()
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)

    service = PrVerificationService(
        verification_repo=verification_repo,
        pr_draft_repo=pr_draft_repo,
        proposal_repo=proposal_repo,
        research_repo=research_repo,
        audit_service=audit_service
    )

    # 1. Draft PR not found
    with pytest.raises(ValueError, match="PR Draft not found"):
        await service.verify_pr_draft("invalid_pr", "admin")

    # 2. Proposal not found
    draft = await pr_draft_repo.create_pr_draft({
        "proposal_id": "invalid_proposal",
        "provider": "github",
        "title": "Fix bug",
        "body": "Fixes bug",
        "risk_level": "LOW"
    })

    with pytest.raises(ValueError, match="Proposal not found"):
        await service.verify_pr_draft(draft["id"], "admin")

    # 3. Successful verification
    proposal = await proposal_repo.create_proposal({
        "research_id": "res_123",
        "title": "Fix Memory",
        "rationale": "Memory leaks",
        "patch_code": (
            "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
            "--- a/apps/bilgeapi/main.py\n"
            "+++ b/apps/bilgeapi/main.py\n"
            "@@ -1,2 +1,3 @@\n"
            "+# fix memory leak\n"
        ),
        "risk_analysis": {"confidence_level": "HIGH"},
        "gate_status": "GATE_PASSED",
        "approval_status": "APPROVED"
    })

    # Update draft to refer to the created proposal
    draft_valid = await pr_draft_repo.create_pr_draft({
        "proposal_id": proposal["id"],
        "provider": "github",
        "title": "Fix bug",
        "body": "Fixes bug",
        "risk_level": "LOW"
    })

    # Add evidence to research request
    await research_repo.create_evidence({
        "research_id": "res_123",
        "source_url": "https://google.com",
        "source_domain": "google.com",
        "content_hash": "hash123",
        "trust_score": 80.0
    })

    verification = await service.verify_pr_draft(draft_valid["id"], "admin")
    assert verification["pr_draft_id"] == draft_valid["id"]
    assert verification["proposal_id"] == proposal["id"]
    assert verification["review_decision"] in ["NEEDS_HUMAN_CAUTION", "REVIEW_READY"]
    assert verification["verification_report"] is not None

    # Check audit events
    events = await audit_repo.list_recent()
    assert any(e.event_type == "PR_VERIFICATION_STARTED" for e in events)
    assert any(e.event_type == "PR_VERIFICATION_COMPLETED" for e in events)
    assert any(e.event_type == "PR_REVIEW_SCORE_ASSIGNED" for e in events)


@pytest.mark.asyncio
async def test_pr_verification_api_endpoints(monkeypatch, test_client_real_auth):
    from bilgeapi.config import settings
    # Enable API Key Auth Mode with role mapping
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator"])

    # Setup test client mock repositories
    from bilgeapi.routers.deps import (
        get_pr_draft_repository,
        get_improvement_repository,
        get_pr_verification_repository,
        get_research_repository
    )
    
    app = test_client_real_auth.app
    pr_draft_repo = app.dependency_overrides[get_pr_draft_repository]()
    proposal_repo = app.dependency_overrides[get_improvement_repository]()
    verification_repo = app.dependency_overrides[get_pr_verification_repository]()
    research_repo = app.dependency_overrides[get_research_repository]()

    # Create dummy proposal
    proposal = await proposal_repo.create_proposal({
        "research_id": "res_abc",
        "title": "Fix DB Lag",
        "rationale": "Optimized indexes",
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

    # 1. Trigger verification (POST /verify) - require admin API key
    headers = {"X-API-Key": "admin_key"}
    
    resp_post = test_client_real_auth.post(f"/v1/improvements/pr-drafts/{draft['id']}/verify", headers=headers)
    assert resp_post.status_code == 201
    ver_data = resp_post.json()
    assert ver_data["pr_draft_id"] == draft["id"]
    assert ver_data["status"] is not None

    # Try verify with non-admin operator -> Access Denied (403)
    op_headers = {"X-API-Key": "op_key"}
    resp_post_fail = test_client_real_auth.post(f"/v1/improvements/pr-drafts/{draft['id']}/verify", headers=op_headers)
    assert resp_post_fail.status_code == 403

    # 2. Get verification record (GET /verification) -> accessible by operator
    resp_get = test_client_real_auth.get(f"/v1/improvements/pr-drafts/{draft['id']}/verification", headers=op_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == ver_data["id"]

    # 3. Get markdown report (GET /review-report) -> accessible by operator
    resp_rep = test_client_real_auth.get(f"/v1/improvements/pr-drafts/{draft['id']}/review-report", headers=op_headers)
    assert resp_rep.status_code == 200
    assert "report_markdown" in resp_rep.json()


def test_sandbox_patch_analyzer_security_threats():
    analyzer = SandboxPatchAnalyzer()

    # Case 1: eval/exec/shell=True
    eval_patch = "+++ b/apps/bilgeapi/main.py\n+eval('1+1')\n"
    res = analyzer.analyze_patch(eval_patch)
    assert res["has_blocked_patterns"] is True

    # Case 2: Destructive DB migration
    migration_patch = "+++ b/apps/bilgeapi/migrations/v1.py\n+op.drop_table('users')\n"
    res = analyzer.analyze_patch(migration_patch)
    assert res["has_destructive_migration"] is True

    # Case 3: Private IP request
    ip_patch = "+++ b/apps/bilgeapi/main.py\n+requests.get('http://127.0.0.1:8500')\n"
    res = analyzer.analyze_patch(ip_patch)
    assert res["has_private_ip_request"] is True

    # Case 4: Force push
    push_patch = "+++ b/apps/bilgeapi/main.py\n+git push --force origin main\n"
    res = analyzer.analyze_patch(push_patch)
    assert res["has_force_push"] is True

    # Case 5: Secret logging
    secret_patch = "+++ b/apps/bilgeapi/main.py\n+logger.info(f'The secret is {api_key}')\n"
    res = analyzer.analyze_patch(secret_patch)
    assert res["has_secret_logging"] is True


def test_pr_gate_scorer_auto_blocked():
    scorer = PrReviewGateScorer()
    
    # Proposal high confidence but dangerous pattern detected
    analysis = {
        "affected_files": ["apps/bilgeapi/main.py"],
        "risky_files": [],
        "test_files": [],
        "patch_size_lines": 10,
        "mutation_commands_detected": False,
        "has_blocked_patterns": True  # auto-blocked
    }
    proposal = {"risk_analysis": {"confidence_level": "HIGH"}}
    res = scorer.calculate_score(analysis, proposal, [])
    assert res["review_decision"] == "BLOCKED"
    assert res["score"] < 50.0
    assert "Dangerous pattern (eval/exec/shell=True)" in res["blocked_reasons"]


def test_sandbox_patch_analyzer_ui_files():
    analyzer = SandboxPatchAnalyzer()

    # Case 1: HTML file modified
    ui_patch = "+++ b/apps/cms/templates/index.html\n+<h1>Welcome</h1>\n"
    res = analyzer.analyze_patch(ui_patch)
    assert "apps/cms/templates/index.html" in res["ui_files"]

    # Case 2: TSX component modified
    tsx_patch = "+++ b/frontend/src/components/Button.tsx\n+const Button = () => <button>Click</button>\n"
    res = analyzer.analyze_patch(tsx_patch)
    assert "frontend/src/components/Button.tsx" in res["ui_files"]

    # Case 3: Python/Backend file - not UI file
    backend_patch = "+++ b/apps/bilgeapi/auth.py\n+def check_auth(): pass\n"
    res = analyzer.analyze_patch(backend_patch)
    assert len(res["ui_files"]) == 0


def test_pr_gate_scorer_ui_visual_evidence():
    scorer = PrReviewGateScorer()

    proposal = {"risk_analysis": {"confidence_level": "HIGH"}}

    # Scenario 1: UI changed, NO visual evidence -> BLOCKED
    analysis_ui = {
        "affected_files": ["frontend/src/components/Button.tsx"],
        "risky_files": [],
        "test_files": [],
        "ui_files": ["frontend/src/components/Button.tsx"],
        "patch_size_lines": 10,
        "mutation_commands_detected": False
    }

    res_no_evidence = scorer.calculate_score(analysis_ui, proposal, [])
    assert res_no_evidence["review_decision"] == "BLOCKED"
    assert any("UI modifications detected without browser-testing" in reason for reason in res_no_evidence["blocked_reasons"])

    # Scenario 2: UI changed, WITH visual evidence -> Passes (NEEDS_HUMAN_CAUTION because of missing test files)
    evidences = [
        {
            "title": "Playwright Visual Test Run",
            "snippet": "Screenshot matches. Trace saved to trace.zip",
            "source_url": "https://ci.company.internal/playwright/trace",
            "trust_score": 85.0
        }
    ]

    res_with_evidence = scorer.calculate_score(analysis_ui, proposal, evidences)
    assert res_with_evidence["review_decision"] != "BLOCKED"
    assert len(res_with_evidence["blocked_reasons"]) == 0


