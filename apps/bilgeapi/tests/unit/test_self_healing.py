import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from bilgeapi.config import settings
from bilgeapi.services.self_healing import (
    SelfHealingPolicy,
    SelfHealingExecutor,
    EmergencyRecoveryService,
    RemediationRunbookRegistry
)
from bilgeapi.services.review_ledger import ReviewLedgerService
from bilgeapi.repositories.memory import (
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

    from bilgeapi.routers.deps import (
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


@pytest.mark.asyncio
async def test_self_healing_skill_gating(monkeypatch):
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
        "max_attempts": 2,
        "cooldown_seconds": 0
    })

    # Mock SkillCheckService
    mock_check_service = AsyncMock()
    
    executor = SelfHealingExecutor(
        finding_repo=finding_repo,
        runbook_repo=runbook_repo,
        attempt_repo=attempt_repo,
        ledger_service=ledger_service,
        skill_check_service=mock_check_service
    )

    # 1. Skill check returns BLOCKED
    mock_check_service.check_patch.return_value = MagicMock(
        status="BLOCKED",
        checks=[MagicMock(reason="Forbidden git action detected")]
    )
    attempt = await executor.execute_remediation(finding["id"], runbook["id"], "test-actor")
    assert attempt["status"] == "HUMAN_GATE_REQUIRED"
    assert "blocked by skill check" in attempt["error_message"]

    # 2. Skill check raises exception (Fail-closed)
    mock_check_service.check_patch.side_effect = Exception("Registry corruption")
    attempt_fail = await executor.execute_remediation(finding["id"], runbook["id"], "test-actor")
    assert attempt_fail["status"] == "HUMAN_GATE_REQUIRED"
    assert "fail-closed" in attempt_fail["error_message"]


async def test_self_healing_circuit_breaker_and_semantic_memory(monkeypatch):
    from bilgeapi.services.self_healing import SelfHealingCircuitBreaker, SemanticRemediationMemory
    
    # 1. Reset state
    SelfHealingCircuitBreaker.reset()
    SemanticRemediationMemory.clear()
    assert SelfHealingCircuitBreaker.is_tripped() is False

    # 2. Record failures on a file
    file_path = "libs/utils/unsafe_code.py"
    SelfHealingCircuitBreaker.record_failure(file_path)
    assert SelfHealingCircuitBreaker.is_tripped() is False
    
    SelfHealingCircuitBreaker.record_failure(file_path)
    assert SelfHealingCircuitBreaker.is_tripped() is False

    # 3rd failure trips the circuit breaker
    SelfHealingCircuitBreaker.record_failure(file_path)
    assert SelfHealingCircuitBreaker.is_tripped() is True
    
    # Reset
    SelfHealingCircuitBreaker.reset()
    assert SelfHealingCircuitBreaker.is_tripped() is False

    # Trip global kill switch
    SelfHealingCircuitBreaker.trip_global_kill_switch()
    assert SelfHealingCircuitBreaker.is_tripped() is True
    SelfHealingCircuitBreaker.reset()

    # 3. Test Semantic Memory Vector and Cosine Similarity
    title1 = "Memory leak in query processor"
    title2 = "Database query processor memory leak detected"
    title3 = "Unauthorized user access alert"
    
    runbook1 = {"id": "rb_leak", "action_type": "restart_worker"}
    runbook2 = {"id": "rb_auth", "action_type": "auto_revoke_key"}

    SemanticRemediationMemory.register_successful_repair(title1, runbook1, 100.0)
    SemanticRemediationMemory.register_successful_repair(title3, runbook2, 100.0)

    # Search for similar incident
    match = SemanticRemediationMemory.find_similar_remediation(title2, threshold=0.3)
    assert match is not None
    assert match["runbook"]["id"] == "rb_leak"

    # Search for unrelated incident
    match_unrelated = SemanticRemediationMemory.find_similar_remediation("Ruff linter error in main.py", threshold=0.9)
    assert match_unrelated is None

    # Test auto runbook extraction
    extracted_rb = SemanticRemediationMemory.extract_runbook_from_successful_patch("SSRF violation in webhook dispatcher", "switch_to_safe_mode")
    assert extracted_rb["action_type"] == "switch_to_safe_mode"
    assert extracted_rb["execution_mode"] == "AUTO_HEALING"
    
    # Verify it has been added to memory
    match_extracted = SemanticRemediationMemory.find_similar_remediation("webhook dispatcher SSRF violation detected", threshold=0.3)
    assert match_extracted is not None
    assert match_extracted["runbook"]["action_type"] == "switch_to_safe_mode"


