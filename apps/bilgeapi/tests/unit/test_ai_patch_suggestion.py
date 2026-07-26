import pytest

from bilgeapi.adapters.ai_patch_provider import MockAIPatchProvider, OpenAIPatchProvider
from bilgeapi.repositories.memory import (
    InMemoryAIPatchSuggestionRepository,
    InMemoryAuditRepository,
    InMemoryImprovementRepository,
    InMemoryPatchRevisionRepository,
    InMemoryPrDraftRepository,
    InMemoryPrReviewFeedbackRepository,
    InMemoryPrVerificationRepository,
    InMemoryResearchRepository,
    InMemoryReviewLedgerRepository,
)
from bilgeapi.services.ai_patch_suggestion import (
    AIPatchSuggestionService,
    PatchSuggestionContextBuilder,
)
from bilgeapi.services.audit import AuditService
from bilgeapi.services.pr_verification import PrVerificationService
from bilgeapi.services.review_ledger import ReviewLedgerService


async def _seed_review_context(
    *,
    pr_draft_repo,
    proposal_repo,
    feedback_repo,
    revision_repo,
    research_repo,
    high_risk_secret=False,
):
    proposal = await proposal_repo.create_proposal(
        {
            "research_id": "res_ai_1",
            "title": "Improve runtime handling",
            "rationale": "Reviewer requested narrower change",
            "patch_code": (
                "diff --git a/apps/bilgeapi/services/runtime.py b/apps/bilgeapi/services/runtime.py\n"
                "--- a/apps/bilgeapi/services/runtime.py\n"
                "+++ b/apps/bilgeapi/services/runtime.py\n"
                "@@ -1,1 +1,2 @@\n"
                "+# existing patch\n"
            ),
            "risk_analysis": {
                "confidence_level": "HIGH",
                "token": "secret-token-value" if high_risk_secret else None,
            },
            "gate_status": "GATE_PASSED",
            "approval_status": "APPROVED",
        }
    )
    pr_draft = await pr_draft_repo.create_pr_draft(
        {
            "proposal_id": proposal["id"],
            "provider": "mock",
            "title": "Draft improvement",
            "body": "Human-reviewable draft body",
            "risk_level": "LOW",
            "risk_flags": [],
        }
    )
    feedback = await feedback_repo.create_feedback(
        {
            "pr_draft_id": pr_draft["id"],
            "reviewer_id": "reviewer_1",
            "comment": "Please reduce scope and add rollback notes.",
        }
    )
    revision = await revision_repo.create_revision(
        {
            "pr_draft_id": pr_draft["id"],
            "feedback_id": feedback["id"],
            "revision_number": 1,
            "revised_patch_code": (
                "diff --git a/apps/bilgeapi/services/runtime.py b/apps/bilgeapi/services/runtime.py\n"
                "--- a/apps/bilgeapi/services/runtime.py\n"
                "+++ b/apps/bilgeapi/services/runtime.py\n"
                "@@ -1,1 +1,2 @@\n"
                "+# revised patch\n"
            ),
            "risk_analysis": {"risk_level": "LOW"},
            "risk_level": "LOW",
        }
    )
    await research_repo.create_evidence(
        {
            "research_id": "res_ai_1",
            "source_url": "https://docs.example.com/runtime",
            "source_domain": "docs.example.com",
            "content_hash": "hash_ai_1",
            "trust_score": 85.0,
        }
    )
    return proposal, pr_draft, feedback, revision


def _build_services():
    suggestion_repo = InMemoryAIPatchSuggestionRepository()
    pr_draft_repo = InMemoryPrDraftRepository()
    proposal_repo = InMemoryImprovementRepository()
    feedback_repo = InMemoryPrReviewFeedbackRepository()
    revision_repo = InMemoryPatchRevisionRepository()
    research_repo = InMemoryResearchRepository()
    verification_repo = InMemoryPrVerificationRepository()
    audit_repo = InMemoryAuditRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    audit_service = AuditService(audit_repo)
    ledger_service = ReviewLedgerService(ledger_repo)
    verification_service = PrVerificationService(
        verification_repo=verification_repo,
        pr_draft_repo=pr_draft_repo,
        proposal_repo=proposal_repo,
        research_repo=research_repo,
        audit_service=audit_service,
        revision_repo=revision_repo,
        ledger_service=ledger_service,
        ai_suggestion_repo=suggestion_repo,
    )
    context_builder = PatchSuggestionContextBuilder(
        pr_draft_repo=pr_draft_repo,
        proposal_repo=proposal_repo,
        feedback_repo=feedback_repo,
        revision_repo=revision_repo,
        research_repo=research_repo,
        ledger_service=ledger_service,
    )
    service = AIPatchSuggestionService(
        suggestion_repo=suggestion_repo,
        pr_draft_repo=pr_draft_repo,
        feedback_repo=feedback_repo,
        revision_repo=revision_repo,
        context_builder=context_builder,
        provider=MockAIPatchProvider(),
        verification_service=verification_service,
        ledger_service=ledger_service,
    )
    return {
        "service": service,
        "suggestion_repo": suggestion_repo,
        "pr_draft_repo": pr_draft_repo,
        "proposal_repo": proposal_repo,
        "feedback_repo": feedback_repo,
        "revision_repo": revision_repo,
        "research_repo": research_repo,
        "verification_repo": verification_repo,
        "ledger_repo": ledger_repo,
        "context_builder": context_builder,
    }


@pytest.mark.asyncio
async def test_mock_provider_and_real_provider_guard():
    provider = MockAIPatchProvider()
    suggestion = await provider.generate_patch_suggestion({"instruction": "narrow scope"})
    assert suggestion["suggested_patch_code"].startswith("diff --git")
    assert suggestion["rationale"]

    real_provider = OpenAIPatchProvider(api_key="secret", model_name="gpt-4.1-mini", allow_real=False)
    with pytest.raises(RuntimeError, match="disabled"):
        await real_provider.generate_patch_suggestion({"instruction": "do not call network"})


@pytest.mark.asyncio
async def test_context_redaction_and_prompt_hash_are_deterministic():
    services = _build_services()
    _, pr_draft, feedback, revision = await _seed_review_context(
        pr_draft_repo=services["pr_draft_repo"],
        proposal_repo=services["proposal_repo"],
        feedback_repo=services["feedback_repo"],
        revision_repo=services["revision_repo"],
        research_repo=services["research_repo"],
        high_risk_secret=True,
    )

    context = await services["context_builder"].build_context(
        pr_draft_id=pr_draft["id"],
        feedback_id=feedback["id"],
        revision_id=revision["id"],
        instruction="Reviewer requested safer rollback.",
    )

    serialized = str(context)
    assert "secret-token-value" not in serialized
    assert "[REDACTED]" in serialized

    service = services["service"]
    first_hash = service.compute_prompt_hash(context, "Reviewer requested safer rollback.")
    second_hash = service.compute_prompt_hash(context, "Reviewer requested safer rollback.")
    assert first_hash == second_hash


@pytest.mark.asyncio
async def test_ai_patch_suggestion_generate_verify_accept_reject_and_ledger():
    services = _build_services()
    _, pr_draft, feedback, revision = await _seed_review_context(
        pr_draft_repo=services["pr_draft_repo"],
        proposal_repo=services["proposal_repo"],
        feedback_repo=services["feedback_repo"],
        revision_repo=services["revision_repo"],
        research_repo=services["research_repo"],
    )

    generated = await services["service"].generate_suggestion(
        pr_draft_id=pr_draft["id"],
        feedback_id=feedback["id"],
        revision_id=revision["id"],
        instruction="Add tests and keep scope narrow.",
        actor_id="admin_1",
    )

    assert generated["status"] == "GENERATED"
    assert generated["provider"] == "mock"
    assert generated["prompt_hash"]
    assert "diff --git" in generated["suggested_patch_code"]

    verification = await services["service"].verify_suggestion(generated["id"], actor_id="admin_1")
    assert verification["ai_suggestion_id"] == generated["id"]
    assert verification["review_decision"] in {"REVIEW_READY", "NEEDS_HUMAN_CAUTION"}

    updated = await services["suggestion_repo"].get_suggestion(generated["id"])
    assert updated["verification_id"] == verification["id"]
    assert updated["status"] == "VERIFIED"

    accepted = await services["service"].accept_for_review(generated["id"], actor_id="admin_1")
    assert accepted["status"] == "ACCEPTED_FOR_REVIEW"

    rejected = await services["service"].reject_suggestion(generated["id"], reason="not needed", actor_id="admin_1")
    assert rejected["status"] == "REJECTED"

    ledger_entries = await services["ledger_repo"].list_by_chain(f"chain_{pr_draft['id']}")
    event_types = {entry["event_type"] for entry in ledger_entries}
    assert "AI_PATCH_SUGGESTION_GENERATED" in event_types
    assert "AI_PATCH_SUGGESTION_VERIFIED" in event_types
    assert "AI_PATCH_SUGGESTION_ACCEPTED_FOR_REVIEW" in event_types
    assert "AI_PATCH_SUGGESTION_REJECTED" in event_types


@pytest.mark.asyncio
async def test_high_risk_ai_suggestion_is_not_review_ready():
    services = _build_services()
    _, pr_draft, feedback, revision = await _seed_review_context(
        pr_draft_repo=services["pr_draft_repo"],
        proposal_repo=services["proposal_repo"],
        feedback_repo=services["feedback_repo"],
        revision_repo=services["revision_repo"],
        research_repo=services["research_repo"],
    )

    generated = await services["service"].generate_suggestion(
        pr_draft_id=pr_draft["id"],
        feedback_id=feedback["id"],
        revision_id=revision["id"],
        instruction="Reviewer asked for auth.py changes with a test.",
        actor_id="admin_1",
    )

    assert generated["risk_level"] == "HIGH"
    verification = await services["service"].verify_suggestion(generated["id"], actor_id="admin_1")
    assert verification["risk_level"] == "HIGH"
    assert verification["review_decision"] == "NEEDS_HUMAN_CAUTION"


@pytest.mark.asyncio
async def test_ai_patch_suggestion_endpoints_rbac(monkeypatch, test_client_real_auth):
    from bilgeapi.config import settings
    from bilgeapi.routers.deps import (
        get_improvement_repository,
        get_patch_revision_repository,
        get_pr_draft_repository,
        get_pr_review_feedback_repository,
        get_research_repository,
    )

    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator"])

    app = test_client_real_auth.app
    proposal_repo = app.dependency_overrides[get_improvement_repository]()
    pr_draft_repo = app.dependency_overrides[get_pr_draft_repository]()
    feedback_repo = app.dependency_overrides[get_pr_review_feedback_repository]()
    revision_repo = app.dependency_overrides[get_patch_revision_repository]()
    research_repo = app.dependency_overrides[get_research_repository]()

    _, pr_draft, feedback, revision = await _seed_review_context(
        pr_draft_repo=pr_draft_repo,
        proposal_repo=proposal_repo,
        feedback_repo=feedback_repo,
        revision_repo=revision_repo,
        research_repo=research_repo,
    )

    payload = {
        "feedback_id": feedback["id"],
        "revision_id": revision["id"],
        "instruction": "Add tests and keep scope narrow.",
    }

    operator_headers = {"X-API-Key": "op_key"}
    admin_headers = {"X-API-Key": "admin_key"}

    forbidden = test_client_real_auth.post(
        f"/v1/improvements/pr-drafts/{pr_draft['id']}/ai-suggestions",
        json=payload,
        headers=operator_headers,
    )
    assert forbidden.status_code == 403

    created = test_client_real_auth.post(
        f"/v1/improvements/pr-drafts/{pr_draft['id']}/ai-suggestions",
        json=payload,
        headers=admin_headers,
    )
    assert created.status_code == 201
    suggestion = created.json()

    listed = test_client_real_auth.get(
        f"/v1/improvements/pr-drafts/{pr_draft['id']}/ai-suggestions",
        headers=operator_headers,
    )
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == suggestion["id"]

    read_one = test_client_real_auth.get(
        f"/v1/improvements/ai-suggestions/{suggestion['id']}",
        headers=operator_headers,
    )
    assert read_one.status_code == 200

    verified = test_client_real_auth.post(
        f"/v1/improvements/ai-suggestions/{suggestion['id']}/verify",
        headers=admin_headers,
    )
    assert verified.status_code == 201
    assert verified.json()["ai_suggestion_id"] == suggestion["id"]

    accepted = test_client_real_auth.post(
        f"/v1/improvements/ai-suggestions/{suggestion['id']}/accept-for-review",
        headers=admin_headers,
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "ACCEPTED_FOR_REVIEW"
