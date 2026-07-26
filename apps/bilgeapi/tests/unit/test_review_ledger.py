import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bilgeapi.models.database import ReviewLedgerEntryModel
from bilgeapi.repositories.memory import (
    InMemoryAuditRepository,
    InMemoryPatchRevisionRepository,
    InMemoryPrDraftRepository,
    InMemoryPrReviewFeedbackRepository,
    InMemoryPrVerificationRepository,
    InMemoryResearchRepository,
    InMemoryImprovementRepository,
    InMemoryReviewLedgerRepository,
)
from bilgeapi.repositories.postgres import PostgresReviewLedgerRepository
from bilgeapi.services.audit import AuditService
from bilgeapi.services.patch_revision import PatchRevisionEngine, ReviewerFeedbackService
from bilgeapi.services.pr_verification import PrVerificationService
from bilgeapi.services.review_ledger import (
    CanonicalPayloadHasher,
    PayloadRedactor,
    ReviewLedgerService,
    ReviewLedgerVerifier,
)


def test_payload_redaction_and_canonical_hashing():
    payload = {
        "api_key": "live-secret",
        "nested": {
            "github_token": "ghp_secret",
            "safe": "visible",
            "raw_content": "copyright-heavy content",
        },
        "items": [{"password": "pw"}, {"comment": "ok"}],
    }

    redacted = PayloadRedactor().redact(payload)

    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["github_token"] == "[REDACTED]"
    assert redacted["nested"]["raw_content"] == "[REDACTED]"
    assert redacted["nested"]["safe"] == "visible"
    assert redacted["items"][0]["password"] == "[REDACTED]"

    hasher = CanonicalPayloadHasher()
    left = hasher.hash_payload({"b": 2, "a": 1})
    right = hasher.hash_payload({"a": 1, "b": 2})

    assert left == right
    assert len(left) == 64


@pytest.mark.asyncio
async def test_review_ledger_append_verify_and_tamper_detection():
    repo = InMemoryReviewLedgerRepository()
    service = ReviewLedgerService(repo)
    verifier = ReviewLedgerVerifier(repo)

    first = await service.append_event(
        chain_id="chain_prd_1",
        event_type="PR_DRAFT_CREATED",
        entity_type="pr_draft",
        entity_id="prd_1",
        actor_id="admin",
        payload={"github_token": "must-not-leak", "risk_level": "LOW"},
    )
    second = await service.append_event(
        chain_id="chain_prd_1",
        event_type="PR_VERIFICATION_COMPLETED",
        entity_type="pr_verification",
        entity_id="prv_1",
        actor_id="admin",
        payload={"review_score": 95, "decision": "REVIEW_READY"},
    )

    assert first["sequence_no"] == 1
    assert second["sequence_no"] == 2
    assert second["previous_hash"] == first["event_hash"]
    assert first["payload_summary"]["github_token"] == "[REDACTED]"

    verified = await verifier.verify_chain("chain_prd_1")
    assert verified["valid"] is True
    assert verified["entry_count"] == 2

    repo_entry = await repo.get_entry(first["id"])
    repo_entry["payload_summary"]["risk_level"] = "HIGH"
    tampered = await verifier.verify_chain("chain_prd_1")

    assert tampered["valid"] is False
    assert any(issue["type"] == "payload_hash_mismatch" for issue in tampered["issues"])


@pytest.mark.asyncio
async def test_review_ledger_retries_on_sequence_conflict():
    class _RetryingRepo(InMemoryReviewLedgerRepository):
        def __init__(self):
            super().__init__()
            self.fail_once = True

        async def append_entry(self, entry_data, tenant_id: str = "default", *args, **kwargs):
            if self.fail_once:
                self.fail_once = False
                raise IntegrityError("insert", {}, Exception("duplicate sequence"))
            return await super().append_entry(entry_data, tenant_id, *args, **kwargs)

    repo = _RetryingRepo()
    service = ReviewLedgerService(repo)

    entry = await service.append_event(
        chain_id="chain_retry",
        event_type="SKILL_HASH_VERIFIED",
        entity_type="skill_registry",
        entity_id="registry",
        actor_id="system",
        payload={"hash": "abc123"},
    )

    assert entry["sequence_no"] == 1
    assert (await repo.list_by_chain("chain_retry"))[0]["id"] == entry["id"]


@pytest.mark.asyncio
async def test_postgres_review_ledger_repository_rolls_back_after_integrity_error():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(ReviewLedgerEntryModel.__table__.create)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        repo = PostgresReviewLedgerRepository(session)

        await repo.append_entry(
            {
                "id": "rle_first",
                "chain_id": "chain_repo_retry",
                "sequence_no": 1,
                "event_type": "FIRST_EVENT",
                "entity_type": "skill_registry",
                "entity_id": "registry",
                "actor_id": "system",
                "previous_hash": None,
                "payload_hash": "hash_1",
                "event_hash": "event_hash_1",
                "payload_summary": {"ok": True},
            }
        )

        with pytest.raises(IntegrityError):
            await repo.append_entry(
                {
                    "id": "rle_duplicate",
                    "chain_id": "chain_repo_retry",
                    "sequence_no": 1,
                    "event_type": "DUPLICATE_EVENT",
                    "entity_type": "skill_registry",
                    "entity_id": "registry",
                    "actor_id": "system",
                    "previous_hash": None,
                    "payload_hash": "hash_2",
                    "event_hash": "event_hash_2",
                    "payload_summary": {"duplicate": True},
                }
            )

        appended = await repo.append_entry(
            {
                "id": "rle_second",
                "chain_id": "chain_repo_retry",
                "sequence_no": 2,
                "event_type": "SECOND_EVENT",
                "entity_type": "skill_registry",
                "entity_id": "registry",
                "actor_id": "system",
                "previous_hash": "event_hash_1",
                "payload_hash": "hash_3",
                "event_hash": "event_hash_3",
                "payload_summary": {"recovered": True},
            }
        )

        assert appended["sequence_no"] == 2
        assert appended["id"] == "rle_second"

    await engine.dispose()


@pytest.mark.asyncio
async def test_review_ledger_endpoint_rbac_and_export(monkeypatch, test_client_real_auth):
    from bilgeapi.config import settings
    from bilgeapi.routers.deps import get_review_ledger_service

    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator"])

    app = test_client_real_auth.app
    ledger_service = app.dependency_overrides[get_review_ledger_service]()

    await ledger_service.append_event(
        chain_id="chain_endpoint",
        event_type="PATCH_REVISION_CREATED",
        entity_type="patch_revision",
        entity_id="prev_1",
        actor_id="admin",
        payload={"secret": "hidden", "revision_number": 1},
    )

    operator_headers = {"X-API-Key": "op_key"}
    admin_headers = {"X-API-Key": "admin_key"}

    recent = test_client_real_auth.get("/v1/review-ledger/recent", headers=operator_headers)
    assert recent.status_code == 200
    assert recent.json()[0]["payload_summary"]["secret"] == "[REDACTED]"

    verify = test_client_real_auth.get("/v1/review-ledger/chains/chain_endpoint/verify", headers=operator_headers)
    assert verify.status_code == 200
    assert verify.json()["valid"] is True

    operator_export = test_client_real_auth.get("/v1/review-ledger/chains/chain_endpoint/export", headers=operator_headers)
    assert operator_export.status_code == 403

    admin_export = test_client_real_auth.get("/v1/review-ledger/chains/chain_endpoint/export", headers=admin_headers)
    assert admin_export.status_code == 200
    assert "PATCH_REVISION_CREATED" in admin_export.json()["content"]


@pytest.mark.asyncio
async def test_feedback_revision_and_verification_write_review_ledger_events():
    audit_repo = InMemoryAuditRepository()
    audit_service = AuditService(audit_repo)
    ledger_repo = InMemoryReviewLedgerRepository()
    ledger_service = ReviewLedgerService(ledger_repo)

    pr_draft_repo = InMemoryPrDraftRepository()
    feedback_repo = InMemoryPrReviewFeedbackRepository()
    revision_repo = InMemoryPatchRevisionRepository()
    verification_repo = InMemoryPrVerificationRepository()
    proposal_repo = InMemoryImprovementRepository()
    research_repo = InMemoryResearchRepository()

    proposal = await proposal_repo.create_proposal(
        {
            "research_id": "res_chain",
            "title": "Ledger flow",
            "rationale": "Evidence-backed change",
            "patch_code": (
                "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
                "+++ b/apps/bilgeapi/main.py\n"
                "+# fix\n"
            ),
            "risk_analysis": {"confidence_level": "HIGH"},
            "gate_status": "GATE_PASSED",
            "approval_status": "APPROVED",
        }
    )
    draft = await pr_draft_repo.create_pr_draft(
        {
            "proposal_id": proposal["id"],
            "provider": "mock",
            "status": "COMPLETED",
            "title": "Draft",
            "body": "Body",
            "risk_level": "LOW",
        }
    )
    await research_repo.create_evidence(
        {
            "research_id": "res_chain",
            "source_url": "https://docs.example.com",
            "source_domain": "docs.example.com",
            "content_hash": "hash",
            "trust_score": 90,
        }
    )

    feedback_service = ReviewerFeedbackService(feedback_repo, pr_draft_repo, audit_service, ledger_service)
    revision_engine = PatchRevisionEngine(revision_repo, pr_draft_repo, audit_service, ledger_service)
    verification_service = PrVerificationService(
        verification_repo=verification_repo,
        pr_draft_repo=pr_draft_repo,
        proposal_repo=proposal_repo,
        research_repo=research_repo,
        audit_service=audit_service,
        revision_repo=revision_repo,
        ledger_service=ledger_service,
    )

    feedback = await feedback_service.add_feedback(draft["id"], "Use safer naming", "reviewer", "operator")
    revision = await revision_engine.create_revision(
        draft["id"],
        feedback["id"],
        (
            "diff --git a/tests/unit/bilgeapi/test_ledger.py b/tests/unit/bilgeapi/test_ledger.py\n"
            "+++ b/tests/unit/bilgeapi/test_ledger.py\n"
            "+def test_flow(): pass\n"
        ),
        "admin",
    )
    verification = await verification_service.verify_revision(revision["id"], "admin")

    entries = await ledger_repo.list_by_chain(f"chain_{draft['id']}")
    event_types = [entry["event_type"] for entry in entries]

    assert "PR_REVIEW_FEEDBACK_ADDED" in event_types
    assert "PATCH_REVISION_CREATED" in event_types
    assert "PATCH_REVISION_VERIFIED" in event_types
    assert verification["revision_id"] == revision["id"]
