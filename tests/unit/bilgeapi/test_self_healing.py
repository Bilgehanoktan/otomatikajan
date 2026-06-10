import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from apps.bilgeapi.config import settings
from apps.bilgeapi.services.self_healing import (
    SelfHealingPolicy,
    SelfHealingExecutor,
    EmergencyRecoveryService,
    RemediationRunbookRegistry
)
from apps.bilgeapi.services.review_ledger import ReviewLedgerService
from apps.bilgeapi.repositories.memory import (
    InMemorySystemFindingRepository,
    InMemoryRemediationRunbookRepository,
    InMemoryRemediationAttemptRepository,
    InMemoryReviewLedgerRepository
)

# ──────────────────────────────────────────────────────────────────────────────
# 1. Unit tests for SelfHealingPolicy
# ──────────────────────────────────────────────────────────────────────────────

def test_policy_low_medium_severity_allowed(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)

    policy = SelfHealingPolicy()

    # LOW finding + safe runbook (requires_human_gate=False)
    finding = {"severity": "LOW", "risk_score": 10}
    runbook = {"action_type": "clear_local_cache", "execution_mode": "AUTO_SAFE", "requires_human_gate": False}
    result = policy.evaluate(finding, runbook)
    assert result["allowed"] is True

    # MEDIUM finding + requires_human_gate=True
    runbook_human = {"action_type": "clear_local_cache", "execution_mode": "AUTO_SAFE", "requires_human_gate": True}
    result = policy.evaluate(finding, runbook_human)
    assert result["allowed"] is False
    assert result["requires_human_gate"] is True


def test_policy_high_severity_blocked(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    policy = SelfHealingPolicy()

    finding = {"severity": "HIGH", "risk_score": 60}
    runbook = {"action_type": "clear_local_cache", "execution_mode": "AUTO_SAFE", "requires_human_gate": False}
    
    result = policy.evaluate(finding, runbook)
    assert result["allowed"] is False
    assert result["requires_human_gate"] is True
    assert "Human Gate" in result["reason"]


def test_policy_critical_liveness_only(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_EMERGENCY_RECOVERY_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)
    policy = SelfHealingPolicy()

    finding = {"severity": "CRITICAL", "risk_score": 85}
    
    # Stateless restart is on liveness recovery whitelist
    runbook_liveness = {"action_type": "restart_stateless_service", "execution_mode": "EMERGENCY_ONLY", "requires_human_gate": False}
    result = policy.evaluate(finding, runbook_liveness)
    assert result["allowed"] is True

    # Other action not on whitelist is blocked
    runbook_other = {"action_type": "retry_failed_job", "execution_mode": "EMERGENCY_ONLY", "requires_human_gate": False}
    result = policy.evaluate(finding, runbook_other)
    assert result["allowed"] is False
    assert result["requires_human_gate"] is True
    assert "liveness recovery" in result["reason"]


def test_policy_forbidden_actions_always_blocked(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    policy = SelfHealingPolicy()

    finding = {"severity": "LOW", "risk_score": 10}
    for forbidden in ["auto_merge", "production_migration_apply", "secret_rotation"]:
        runbook = {"action_type": forbidden, "execution_mode": "AUTO_SAFE", "requires_human_gate": False}
        result = policy.evaluate(finding, runbook)
        assert result["allowed"] is False
        assert result["requires_human_gate"] is True
        assert "explicitly forbidden" in result["reason"]


def test_policy_global_switch_disabled(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", False)
    policy = SelfHealingPolicy()

    finding = {"severity": "LOW", "risk_score": 15}
    runbook = {"action_type": "clear_local_cache", "execution_mode": "AUTO_SAFE", "requires_human_gate": False}
    result = policy.evaluate(finding, runbook)
    assert result["allowed"] is False
    assert "disabled globally" in result["reason"]

# ──────────────────────────────────────────────────────────────────────────────
# 2. Unit tests for SelfHealingExecutor
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_executor_execution_success(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)

    finding_repo = InMemorySystemFindingRepository()
    runbook_repo = InMemoryRemediationRunbookRepository()
    attempt_repo = InMemoryRemediationAttemptRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    ledger_service = ReviewLedgerService(ledger_repo)

    finding = await finding_repo.create_finding({
        "tenant_id": "t1",
        "source_type": "worker",
        "source_id": "w1",
        "source_hash": "h1",
        "title": "Worker Stuck",
        "description": "Worker has been stuck for 5m",
        "severity": "MEDIUM",
        "risk_score": 30.0,
        "status": "OPEN",
    })

    runbook = await runbook_repo.create_runbook({
        "name": "Restart Worker",
        "action_type": "restart_worker",
        "severity_allowed": "MEDIUM",
        "requires_human_gate": False,
        "enabled": True,
        "execution_mode": "AUTO_SAFE",
        "max_attempts": 2,
        "cooldown_seconds": 60
    })

    executor = SelfHealingExecutor(
        finding_repo=finding_repo,
        runbook_repo=runbook_repo,
        attempt_repo=attempt_repo,
        ledger_service=ledger_service
    )

    attempt = await executor.execute_remediation(finding["id"], runbook["id"], "test-actor")
    assert attempt["status"] == "SUCCEEDED"
    assert attempt["attempt_no"] == 1
    assert attempt["before_health"]["status"] == "HEALTHY"
    assert attempt["after_health"]["status"] == "HEALTHY"
    assert "restarted successfully" in attempt["output_summary"]
    
    # Finding should be RESOLVED
    updated_finding = await finding_repo.get_finding(finding["id"])
    assert updated_finding["status"] == "RESOLVED"

    # Ledger event should be present
    entries = await ledger_repo.list_by_chain(chain_id=f"remediation_{finding['id']}")
    assert len(entries) == 2
    assert entries[0]["event_type"] == "REMEDIATION_ATTEMPT_STARTED"
    assert entries[1]["event_type"] == "REMEDIATION_ATTEMPT_SUCCEEDED"


@pytest.mark.asyncio
async def test_executor_max_attempts_blocked(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)

    finding_repo = InMemorySystemFindingRepository()
    runbook_repo = InMemoryRemediationRunbookRepository()
    attempt_repo = InMemoryRemediationAttemptRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    ledger_service = ReviewLedgerService(ledger_repo)

    finding = await finding_repo.create_finding({
        "tenant_id": "t1",
        "source_type": "worker",
        "source_id": "w1",
        "source_hash": "h1",
        "title": "Worker Stuck",
        "description": "Worker stuck",
        "severity": "MEDIUM",
        "risk_score": 30.0,
        "status": "OPEN",
    })

    runbook = await runbook_repo.create_runbook({
        "name": "Restart Worker",
        "action_type": "restart_worker",
        "severity_allowed": "MEDIUM",
        "requires_human_gate": False,
        "enabled": True,
        "execution_mode": "AUTO_SAFE",
        "max_attempts": 1,
        "cooldown_seconds": 0
    })

    executor = SelfHealingExecutor(
        finding_repo=finding_repo,
        runbook_repo=runbook_repo,
        attempt_repo=attempt_repo,
        ledger_service=ledger_service
    )

    # First attempt (allowed)
    att1 = await executor.execute_remediation(finding["id"], runbook["id"], "test-actor")
    assert att1["status"] == "SUCCEEDED"

    # Reset finding to OPEN to try again
    await finding_repo.create_finding({**finding, "status": "OPEN"})

    # Second attempt should be blocked by max_attempts limit (limit is 1)
    att2 = await executor.execute_remediation(finding["id"], runbook["id"], "test-actor")
    assert att2["status"] == "BLOCKED"
    assert att2["attempt_no"] == 2
    assert "max attempts 1 exceeded" in att2["error_message"]

    # Ledger event should indicate blocked
    entries = await ledger_repo.list_by_chain(chain_id=f"remediation_{finding['id']}")
    blocked_entries = [e for e in entries if e["event_type"] == "REMEDIATION_ATTEMPT_BLOCKED"]
    assert len(blocked_entries) == 1
    assert blocked_entries[0]["payload_summary"]["reason"] == "Max attempts exceeded"


@pytest.mark.asyncio
async def test_executor_cooldown_blocked(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)

    finding_repo = InMemorySystemFindingRepository()
    runbook_repo = InMemoryRemediationRunbookRepository()
    attempt_repo = InMemoryRemediationAttemptRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    ledger_service = ReviewLedgerService(ledger_repo)

    finding = await finding_repo.create_finding({
        "tenant_id": "t1",
        "source_type": "worker",
        "source_id": "w1",
        "source_hash": "h1",
        "title": "Worker Stuck",
        "description": "Worker stuck",
        "severity": "MEDIUM",
        "risk_score": 30.0,
        "status": "OPEN",
    })

    runbook = await runbook_repo.create_runbook({
        "name": "Restart Worker",
        "action_type": "restart_worker",
        "severity_allowed": "MEDIUM",
        "requires_human_gate": False,
        "enabled": True,
        "execution_mode": "AUTO_SAFE",
        "max_attempts": 3,
        "cooldown_seconds": 60
    })

    executor = SelfHealingExecutor(
        finding_repo=finding_repo,
        runbook_repo=runbook_repo,
        attempt_repo=attempt_repo,
        ledger_service=ledger_service
    )

    # First attempt (allowed)
    att1 = await executor.execute_remediation(finding["id"], runbook["id"], "test-actor")
    assert att1["status"] == "SUCCEEDED"

    # Reset finding to OPEN
    await finding_repo.create_finding({**finding, "status": "OPEN"})

    # Second attempt immediately should be blocked by cooldown (60 seconds)
    att2 = await executor.execute_remediation(finding["id"], runbook["id"], "test-actor")
    assert att2["status"] == "BLOCKED"
    assert "blocked by cooldown" in att2["error_message"]

    # Ledger event should indicate blocked by cooldown
    entries = await ledger_repo.list_by_chain(chain_id=f"remediation_{finding['id']}")
    blocked_entries = [e for e in entries if e["event_type"] == "REMEDIATION_ATTEMPT_BLOCKED"]
    assert len(blocked_entries) == 1
    assert blocked_entries[0]["payload_summary"]["reason"] == "Cooldown limit exceeded"


@pytest.mark.asyncio
async def test_executor_failure_risk_escalation(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)

    finding_repo = InMemorySystemFindingRepository()
    runbook_repo = InMemoryRemediationRunbookRepository()
    attempt_repo = InMemoryRemediationAttemptRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    ledger_service = ReviewLedgerService(ledger_repo)

    finding = await finding_repo.create_finding({
        "tenant_id": "t1",
        "source_type": "worker",
        "source_id": "w1",
        "source_hash": "h1",
        "title": "Worker Stuck",
        "description": "Worker stuck",
        "severity": "MEDIUM",
        "risk_score": 30.0,
        "status": "OPEN",
    })

    # Action handler returns unknown action, leading to FAILED status
    runbook = await runbook_repo.create_runbook({
        "name": "Failed Action Runbook",
        "action_type": "unknown_action_type",
        "severity_allowed": "MEDIUM",
        "requires_human_gate": False,
        "enabled": True,
        "execution_mode": "AUTO_SAFE",
        "max_attempts": 2,
        "cooldown_seconds": 0
    })

    executor = SelfHealingExecutor(
        finding_repo=finding_repo,
        runbook_repo=runbook_repo,
        attempt_repo=attempt_repo,
        ledger_service=ledger_service
    )

    attempt = await executor.execute_remediation(finding["id"], runbook["id"], "test-actor")
    assert attempt["status"] == "FAILED"

    # Finding risk score should be escalated (+15.0)
    updated_finding = await finding_repo.get_finding(finding["id"])
    assert updated_finding["risk_score"] == 45.0
    assert "Remediation failed" in updated_finding["description"]

# ──────────────────────────────────────────────────────────────────────────────
# 3. Unit tests for EmergencyRecoveryService
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_emergency_recovery_flow(monkeypatch):
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_EMERGENCY_RECOVERY_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)

    finding_repo = InMemorySystemFindingRepository()
    runbook_repo = InMemoryRemediationRunbookRepository()
    attempt_repo = InMemoryRemediationAttemptRepository()
    ledger_repo = InMemoryReviewLedgerRepository()
    ledger_service = ReviewLedgerService(ledger_repo)

    # CRITICAL severity is required
    finding = await finding_repo.create_finding({
        "tenant_id": "t1",
        "source_type": "gateway",
        "source_id": "gw1",
        "source_hash": "h1",
        "title": "Gateway Down",
        "description": "Unreachable gateway",
        "severity": "CRITICAL",
        "risk_score": 90.0,
        "status": "OPEN",
    })

    executor = SelfHealingExecutor(
        finding_repo=finding_repo,
        runbook_repo=runbook_repo,
        attempt_repo=attempt_repo,
        ledger_service=ledger_service
    )
    recovery_service = EmergencyRecoveryService(executor, ledger_service)

    # Execute valid liveness recovery action: restart_stateless_service
    attempt = await recovery_service.run_emergency_recovery(
        finding_id=finding["id"],
        action_type="restart_stateless_service",
        actor_id="admin-actor"
    )
    assert attempt["status"] == "SUCCEEDED"

    # Check ledger entries for emergency recovery
    entries = await ledger_repo.list_by_chain(chain_id=f"emergency_recovery_{finding['id']}")
    assert len(entries) == 2
    assert entries[0]["event_type"] == "EMERGENCY_RECOVERY_STARTED"
    assert entries[1]["event_type"] == "EMERGENCY_RECOVERY_SUCCEEDED"

    # Check non-whitelist liveness recovery action fails
    with pytest.raises(ValueError, match="not a valid liveness recovery action"):
        await recovery_service.run_emergency_recovery(
            finding_id=finding["id"],
            action_type="retry_failed_job",
            actor_id="admin-actor"
        )

# ──────────────────────────────────────────────────────────────────────────────
# 4. End-to-End API / Endpoint / RBAC tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_self_healing_endpoints_rbac(monkeypatch, test_client_real_auth):
    monkeypatch.setattr(settings, "BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setattr(settings, "BILGEAPI_STATIC_KEYS", ["admin_key:admin", "op_key:operator"])
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_EMERGENCY_RECOVERY_ENABLED", True)
    monkeypatch.setattr(settings, "BILGEAPI_SELF_HEALING_SAFE_MODE", False)

    from apps.bilgeapi.routers.deps import (
        get_system_finding_repository,
        get_remediation_runbook_repository,
        get_remediation_attempt_repository
    )

    app = test_client_real_auth.app
    finding_repo = app.dependency_overrides[get_system_finding_repository]()
    runbook_repo = app.dependency_overrides[get_remediation_runbook_repository]()
    attempt_repo = app.dependency_overrides[get_remediation_attempt_repository]()

    finding = await finding_repo.create_finding({
        "tenant_id": "t1",
        "source_type": "worker",
        "source_id": "w1",
        "source_hash": "h1",
        "title": "Worker Stuck",
        "description": "Worker stuck",
        "severity": "MEDIUM",
        "risk_score": 30.0,
        "status": "OPEN",
    })

    runbook = await runbook_repo.create_runbook({
        "name": "Restart Worker",
        "action_type": "restart_worker",
        "severity_allowed": "MEDIUM",
        "requires_human_gate": False,
        "enabled": True,
        "execution_mode": "AUTO_SAFE",
        "max_attempts": 2,
        "cooldown_seconds": 60
    })

    op_headers = {"X-API-Key": "op_key"}
    admin_headers = {"X-API-Key": "admin_key"}

    # 1. Test List Runbooks (Operator gets 200, Admin gets 200)
    resp = test_client_real_auth.get("/v1/watchdog/runbooks", headers=op_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # 2. Test Runbook Enable/Disable (Operator gets 403, Admin gets 200)
    resp = test_client_real_auth.post(f"/v1/watchdog/runbooks/{runbook['id']}/disable", headers=op_headers)
    assert resp.status_code == 403

    resp = test_client_real_auth.post(f"/v1/watchdog/runbooks/{runbook['id']}/disable", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False

    resp = test_client_real_auth.post(f"/v1/watchdog/runbooks/{runbook['id']}/enable", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True

    # 3. Test Trigger Remediation (Operator gets 403, Admin gets 200)
    resp = test_client_real_auth.post(
        f"/v1/watchdog/findings/{finding['id']}/remediate",
        json={"runbook_id": runbook["id"]},
        headers=op_headers
    )
    assert resp.status_code == 403

    resp = test_client_real_auth.post(
        f"/v1/watchdog/findings/{finding['id']}/remediate",
        json={"runbook_id": runbook["id"]},
        headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUCCEEDED"
    attempt_id = resp.json()["id"]

    # 4. Test List attempts & Get attempt (Operator gets 200)
    resp = test_client_real_auth.get("/v1/watchdog/remediations", headers=op_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = test_client_real_auth.get(f"/v1/watchdog/remediations/{attempt_id}", headers=op_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUCCEEDED"

    # 5. Test Emergency Recovery Endpoint (Operator gets 403, Admin gets 200)
    crit_finding = await finding_repo.create_finding({
        "tenant_id": "t1",
        "source_type": "gateway",
        "source_id": "gw1",
        "source_hash": "h_crit",
        "title": "API Gateway Down",
        "description": "Gateway unreachable",
        "severity": "CRITICAL",
        "risk_score": 90.0,
        "status": "OPEN",
    })

    resp = test_client_real_auth.post(
        "/v1/watchdog/emergency-recovery/run",
        json={"finding_id": crit_finding["id"], "action_type": "restart_stateless_service"},
        headers=op_headers
    )
    assert resp.status_code == 403

    resp = test_client_real_auth.post(
        "/v1/watchdog/emergency-recovery/run",
        json={"finding_id": crit_finding["id"], "action_type": "restart_stateless_service"},
        headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUCCEEDED"
