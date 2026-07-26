import pytest

from bilgeapi.repositories.memory import (
    InMemoryReleaseCheckRepository,
    InMemoryReviewLedgerRepository,
    InMemorySystemFindingRepository,
)
from bilgeapi.services.review_ledger import ReviewLedgerService
from bilgeapi.services.system_watchdog import (
    ActingGovernorPolicy,
    SystemFindingService,
    SystemRiskScorer,
    SystemSignalCollector,
    SystemWatchdogService,
    WatchdogEvidenceBuilder,
    WatchdogSignal,
)


def test_system_risk_scorer_scores_and_severity():
    scorer = SystemRiskScorer()
    assert scorer.severity_for_score(10) == "LOW"
    assert scorer.severity_for_score(30) == "MEDIUM"
    assert scorer.severity_for_score(60) == "HIGH"
    assert scorer.severity_for_score(80) == "CRITICAL"

    scored = scorer.score_signal(WatchdogSignal(
        source_type="release_gate",
        source_id="rel_bad",
        title="Release gate blocker detected",
        description="blocker",
        risk_points=100,
        evidence={"blockers": ["db mismatch"]},
    ))
    assert scored["risk_score"] == 100.0
    assert scored["severity"] == "CRITICAL"


@pytest.mark.asyncio
async def test_release_gate_blocker_creates_critical_finding(monkeypatch):
    monkeypatch.setenv("BILGEAPI_WATCHDOG_ENABLED", "true")
    release_repo = InMemoryReleaseCheckRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    finding_repo = InMemorySystemFindingRepository()
    ledger_service = ReviewLedgerService(ledger_repo)

    await release_repo.create_check({
        "id": "rel_blocked",
        "status": "BLOCKED",
        "score": 65.0,
        "blockers": ["migration mismatch"],
        "warnings": [],
    })

    service = SystemWatchdogService(
        finding_service=SystemFindingService(finding_repo, ledger_service),
        collector=SystemSignalCollector(release_repo=release_repo, ledger_repo=ledger_repo),
        ledger_service=ledger_service,
    )
    result = await service.run_scan("admin")

    assert result["status"] == "COMPLETED"
    assert result["findings_created"] == 1
    assert result["findings"][0]["severity"] == "CRITICAL"
    assert result["findings"][0]["status"] == "HUMAN_GATE_REQUIRED"


@pytest.mark.asyncio
async def test_ledger_invalid_signal_can_create_high_or_critical_finding(monkeypatch):
    monkeypatch.setenv("BILGEAPI_WATCHDOG_ENABLED", "true")
    finding_repo = InMemorySystemFindingRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    ledger_service = ReviewLedgerService(ledger_repo)
    finding_service = SystemFindingService(finding_repo, ledger_service)
    scorer = SystemRiskScorer()

    scored = scorer.score_signal(WatchdogSignal(
        source_type="review_ledger",
        source_id="chain-invalid",
        title="Ledger invalid",
        description="Hash chain validation failed.",
        risk_points=80,
        evidence={"valid": False, "chain_id": "chain-invalid"},
    ))
    result = await finding_service.find_or_create_from_signal(scored, "admin", "corr_ledger")

    assert result["created"] is True
    assert result["finding"]["severity"] == "CRITICAL"


@pytest.mark.asyncio
async def test_finding_dedupe_and_terminal_no_reopen(monkeypatch):
    monkeypatch.setenv("BILGEAPI_WATCHDOG_ENABLED", "true")
    finding_repo = InMemorySystemFindingRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    finding_service = SystemFindingService(finding_repo, ReviewLedgerService(ledger_repo))
    scored = SystemRiskScorer().score_signal(WatchdogSignal(
        source_type="release_gate",
        source_id="rel_same",
        title="Release gate warning detected",
        description="warning",
        risk_points=35,
        evidence={"warnings": 1},
    ))

    first = await finding_service.find_or_create_from_signal(scored, "admin", "corr_1")
    second = await finding_service.find_or_create_from_signal(scored, "admin", "corr_2")

    assert first["created"] is True
    assert second["deduped"] is True
    assert second["finding"]["id"] == first["finding"]["id"]
    assert second["finding"]["occurrence_count"] == 2

    dismissed = await finding_service.dismiss(first["finding"]["id"], "admin")
    assert dismissed["status"] == "DISMISSED"

    third = await finding_service.find_or_create_from_signal(scored, "admin", "corr_3")
    assert third.get("terminal") is True
    assert third["created"] is False
    assert third["finding"]["occurrence_count"] == 2

    with pytest.raises(ValueError, match="terminal"):
        await finding_service.acknowledge(first["finding"]["id"], "admin")


def test_acting_governor_policy_never_allows_forbidden_actions():
    policy = ActingGovernorPolicy()
    recommendation = policy.recommendation_for({
        "severity": "CRITICAL",
        "recommended_action": None,
    })
    assert "auto_merge" in recommendation["forbidden_actions"]
    assert "auto_deploy" in recommendation["forbidden_actions"]
    assert "auto_revoke_key" in recommendation["forbidden_actions"]
    assert "production_migration_apply" in recommendation["forbidden_actions"]


def test_watchdog_evidence_redaction():
    evidence = WatchdogEvidenceBuilder().build({
        "source_type": "config",
        "source_id": "secret-test",
        "risk_score": 80,
        "severity": "CRITICAL",
        "evidence": {
            "api_key": "blg_live_secret",
            "token": "ghp_secret",
            "nested": {"webhook_secret": "super-secret"},
        },
        "links": {},
    })
    assert evidence["evidence"]["api_key"] == "[REDACTED]"
    assert evidence["evidence"]["token"] == "[REDACTED]"
    assert evidence["evidence"]["nested"]["webhook_secret"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_watchdog_disabled_returns_safe_noop(monkeypatch):
    monkeypatch.setenv("BILGEAPI_WATCHDOG_ENABLED", "false")
    service = SystemWatchdogService(
        finding_service=SystemFindingService(InMemorySystemFindingRepository()),
        collector=SystemSignalCollector(),
    )
    result = await service.run_scan("admin")
    assert result["status"] == "DISABLED"
    assert result["findings_created"] == 0
    assert "auto_merge" in result["forbidden_actions"]


@pytest.mark.asyncio
async def test_production_requires_human_gate(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED", "false")
    monkeypatch.setenv("BILGEAPI_WATCHDOG_ENABLED", "true")
    service = SystemWatchdogService(
        finding_service=SystemFindingService(InMemorySystemFindingRepository()),
        collector=SystemSignalCollector(),
    )
    with pytest.raises(ValueError, match="HUMAN_GATE_REQUIRED"):
        await service.run_scan("admin")


@pytest.mark.asyncio
async def test_watchdog_endpoints_rbac(monkeypatch, test_client_real_auth):
    from bilgeapi.config import settings
    from bilgeapi.routers.deps import get_release_repository, get_system_finding_repository

    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator"])
    monkeypatch.setenv("BILGEAPI_WATCHDOG_ENABLED", "true")

    app = test_client_real_auth.app
    release_repo = app.dependency_overrides[get_release_repository]()
    finding_repo = app.dependency_overrides[get_system_finding_repository]()
    await release_repo.create_check({
        "id": "rel_warning_api",
        "status": "WARNING",
        "score": 90.0,
        "blockers": [],
        "warnings": ["warning"],
    })

    op_headers = {"X-API-Key": "op_key"}
    admin_headers = {"X-API-Key": "admin_key"}

    op_run = test_client_real_auth.post("/v1/watchdog/run", headers=op_headers)
    assert op_run.status_code == 403

    admin_run = test_client_real_auth.post("/v1/watchdog/run", headers=admin_headers)
    assert admin_run.status_code == 200
    finding = admin_run.json()["findings"][0]

    status_resp = test_client_real_auth.get("/v1/watchdog/status", headers=op_headers)
    assert status_resp.status_code == 200

    findings_resp = test_client_real_auth.get("/v1/watchdog/findings", headers=op_headers)
    assert findings_resp.status_code == 200
    assert len(findings_resp.json()) == 1

    op_ack = test_client_real_auth.post(
        f"/v1/watchdog/findings/{finding['id']}/acknowledge",
        headers=op_headers,
    )
    assert op_ack.status_code == 403

    admin_ack = test_client_real_auth.post(
        f"/v1/watchdog/findings/{finding['id']}/acknowledge",
        headers=admin_headers,
    )
    assert admin_ack.status_code == 200
    assert admin_ack.json()["status"] == "ACKNOWLEDGED"

    admin_dismiss = test_client_real_auth.post(
        f"/v1/watchdog/findings/{finding['id']}/dismiss",
        headers=admin_headers,
    )
    assert admin_dismiss.status_code == 200
    assert admin_dismiss.json()["status"] == "DISMISSED"

    saved = await finding_repo.get_finding(finding["id"])
    assert saved["status"] == "DISMISSED"
