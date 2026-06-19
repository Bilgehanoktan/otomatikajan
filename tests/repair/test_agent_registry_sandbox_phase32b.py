import os
import sys
import uuid
import pytest
import shutil
import hashlib
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from libs.db.models import Base
from libs.db.session import get_db
from libs.db.models.repair_models import AgentCapabilityModel, AgentRunModel
from libs.db.models.governance_models import GovernanceProofEventRecord
from services.repair.external_agents.agent_capability_registry import AgentCapabilityRegistry
from services.repair.external_agents.agent_policy_engine import AgentPolicyEngine
from services.repair.external_agents.agent_sandbox_executor import AgentSandboxExecutor
from services.repair.external_agents.agent_ledger_reporter import AgentLedgerReporter

@pytest.fixture
async def test_db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def test_db_session(test_db_engine):
    async_session = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def test_api_client(test_db_session):
    from apps.public_api.main import app
    
    async def override_get_db():
        yield test_db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    # Override SIF identity checks to return an admin identity bypass
    async def override_get_identity():
        return {"id": uuid.uuid4(), "email": "admin@sovereign.agi", "name": "admin", "role": "SOVEREIGN_PRIME", "type": "operator"}
        
    async def override_require_permission():
        return {"id": uuid.uuid4(), "email": "admin@sovereign.agi", "name": "admin", "role": "SOVEREIGN_PRIME", "type": "operator"}

    from services.auth.jwt_auth import get_current_identity, require_permission
    
    app.dependency_overrides[get_current_identity] = override_get_identity
    
    # We must override specific dependecies if they are called inside require_permission
    app.dependency_overrides[require_permission("agents.read")] = override_require_permission
    app.dependency_overrides[require_permission("agents.manage")] = override_require_permission
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_registry_seeding_and_toggles(test_db_session):
    # 1. Seeding default agent records
    await AgentCapabilityRegistry.initialize_defaults(test_db_session)
    
    # 2. Verify all 7 agents exist and are disabled by default
    agents_keys = ["swe_agent", "pr_agent", "stagehand", "openhands", "browser_agent", "test_gen_agent", "code_review_agent"]
    for key in agents_keys:
        cap = await AgentCapabilityRegistry.get_agent_capability(test_db_session, key)
        assert cap is not None
        assert cap.enabled is False
        assert cap.requires_human_approval is True
        
        # Verify specific defaults matching instructions
        if key in ["pr_agent", "stagehand", "browser_agent", "code_review_agent"]:
            assert cap.sandbox_mode == "read-only"
        else:
            assert cap.sandbox_mode == "workspace-write"

    # 3. Test enable/disable toggles
    swe_cap = await AgentCapabilityRegistry.get_agent_capability(test_db_session, "swe_agent")
    assert swe_cap.enabled is False
    
    swe_cap.enabled = True
    await test_db_session.commit()
    
    updated_cap = await AgentCapabilityRegistry.get_agent_capability(test_db_session, "swe_agent")
    assert updated_cap.enabled is True


@pytest.mark.asyncio
async def test_policy_engine_validations(test_db_session, tmp_path):
    await AgentCapabilityRegistry.initialize_defaults(test_db_session)
    
    # Disabled agent should fail validation
    valid, reason = await AgentPolicyEngine.validate_execution(
        db=test_db_session,
        agent_key="swe_agent",
        command_handler="run_tests",
        target_paths=["tests/ui_repair"],
        cost=1.0,
        workspace_root=tmp_path
    )
    assert valid is False
    assert "is disabled" in reason

    # Enable swe_agent to test boundaries
    swe_cap = await AgentCapabilityRegistry.get_agent_capability(test_db_session, "swe_agent")
    swe_cap.enabled = True
    await test_db_session.commit()

    # Valid run command and path
    valid, reason = await AgentPolicyEngine.validate_execution(
        db=test_db_session,
        agent_key="swe_agent",
        command_handler="run_tests",
        target_paths=["tests/ui_repair"],
        cost=1.0,
        workspace_root=tmp_path
    )
    assert valid is True

    # 1. Blocked commands check (unregistered handler)
    valid, reason = await AgentPolicyEngine.validate_execution(
        db=test_db_session,
        agent_key="swe_agent",
        command_handler="rm_rf_system",
        target_paths=["tests/ui_repair"],
        cost=1.0,
        workspace_root=tmp_path
    )
    assert valid is False
    assert "is not allowed" in reason

    # 2. Blocked directory check (libs/db)
    valid, reason = await AgentPolicyEngine.validate_execution(
        db=test_db_session,
        agent_key="swe_agent",
        command_handler="run_tests",
        target_paths=["libs/db/session.py"],
        cost=1.0,
        workspace_root=tmp_path
    )
    assert valid is False
    assert "is blocked by policy" in reason

    # 3. Path traversal escape (../ outside root)
    valid, reason = await AgentPolicyEngine.validate_execution(
        db=test_db_session,
        agent_key="swe_agent",
        command_handler="run_tests",
        target_paths=["../../etc/passwd"],
        cost=1.0,
        workspace_root=tmp_path
    )
    assert valid is False
    assert "Path traversal or escape" in reason

    # 4. Budget limit overflow
    valid, reason = await AgentPolicyEngine.validate_execution(
        db=test_db_session,
        agent_key="swe_agent",
        command_handler="run_tests",
        target_paths=["tests/ui_repair"],
        cost=50.0, # max_cost_limit is 10.0
        workspace_root=tmp_path
    )
    assert valid is False
    assert "exceeds agent's max cost limit" in reason

    # 5. Network restriction check
    valid, reason = await AgentPolicyEngine.validate_execution(
        db=test_db_session,
        agent_key="swe_agent",
        command_handler="run_tests",
        target_paths=["tests/ui_repair"],
        cost=1.0,
        workspace_root=tmp_path,
        network_domains=["google.com"]
    )
    assert valid is False
    assert "Network access is disabled" in reason


@pytest.mark.asyncio
async def test_ledger_redaction_and_truncation(test_db_session):
    # Test redaction of sensitive patterns
    dirty_text = "Connected to postgresql://user:my-secret-pass@localhost:5432/db api_key=1234567890abcdef token=eyJhbGciOiJIUzI1NiJ9.ey"
    clean_text = AgentLedgerReporter.redact_secrets(dirty_text)
    assert "my-secret-pass" not in clean_text
    assert "1234567890abcdef" not in clean_text
    assert "[REDACTED]" in clean_text

    # Test truncation limits
    long_text = "A" * 25000
    short_text = AgentLedgerReporter.truncate_text(long_text, max_chars=100)
    assert len(short_text) == 136 # 100 + warning suffix
    assert "[TRUNCATED" in short_text

    # Create run record and verify hashes & events
    run_id = "run-test-ledgers"
    await AgentLedgerReporter.create_run_record(
        db=test_db_session,
        run_id=run_id,
        agent_key="swe_agent",
        input_parameters={"param": "value"},
        sandbox_mode="read-only",
        network_policy="disabled"
    )

    # Verify run record in DB
    run_stmt = select(AgentRunModel).where(AgentRunModel.run_id == run_id)
    res = await test_db_session.execute(run_stmt)
    run = res.scalars().first()
    assert run is not None
    assert run.status == "PENDING"
    assert run.input_hash == AgentLedgerReporter.compute_sha256({"param": "value"})

    # Complete the run record
    await AgentLedgerReporter.complete_run_record(
        db=test_db_session,
        run_id=run_id,
        exit_code=0,
        stdout="clean log",
        stderr="clean err",
        cost=0.02,
        commands_executed=["pytest"],
        policy_violations=[]
    )

    # Re-verify finished run record
    await test_db_session.refresh(run)
    assert run.status == "COMPLETED"
    assert run.exit_code == 0
    assert run.stdout == "clean log"
    assert run.output_hash == AgentLedgerReporter.compute_sha256({"stdout": "clean log", "stderr": "clean err"})


@pytest.mark.asyncio
async def test_sandbox_executor_read_only(test_db_session):
    await AgentCapabilityRegistry.initialize_defaults(test_db_session)
    
    # Enable code_review_agent (which is read-only)
    cap = await AgentCapabilityRegistry.get_agent_capability(test_db_session, "code_review_agent")
    cap.enabled = True
    await test_db_session.commit()

    run_id = "run-sandbox-ro-test"
    
    success, output, workspace_path = await AgentSandboxExecutor.execute_run(
        db=test_db_session,
        run_id=run_id,
        agent_key="code_review_agent",
        command_handler="inspect_repo",
        arguments={"target_file": "services/ui_repair/service.py"},
        target_paths=["services/ui_repair/service.py"],
        cost=0.01
    )
    
    assert success is True
    assert "class UIRepairService" in output or "import" in output
    # Read-only executor must clean up/delete the temp workspace
    assert workspace_path is None


@pytest.mark.asyncio
async def test_sandbox_executor_workspace_write(test_db_session):
    await AgentCapabilityRegistry.initialize_defaults(test_db_session)
    
    # Enable test_gen_agent (which is workspace-write)
    cap = await AgentCapabilityRegistry.get_agent_capability(test_db_session, "test_gen_agent")
    cap.enabled = True
    await test_db_session.commit()

    run_id = "run-sandbox-ww-test"
    
    # Generate mock patch
    success, output, workspace_path = await AgentSandboxExecutor.execute_run(
        db=test_db_session,
        run_id=run_id,
        agent_key="test_gen_agent",
        command_handler="generate_patch",
        arguments={"patch_content": "diff content", "output_patch_path": "new_test.patch"},
        target_paths=["tests/new_test.patch"],
        cost=0.01
    )
    
    assert success is True
    assert "Patch generated" in output
    assert workspace_path is not None
    
    # Verify that the patch file was generated in the temporary preserved workspace
    ww_path = Path(workspace_path)
    assert ww_path.exists()
    assert (ww_path / "new_test.patch").exists()
    assert (ww_path / "new_test.patch").read_text(encoding="utf-8") == "diff content"
    
    # Verify main repo is NOT contaminated
    from services.repair.evidence_pack import REPO_ROOT
    assert not (REPO_ROOT / "new_test.patch").exists()

    # Clean up preserved workspace
    shutil.rmtree(ww_path.parent, ignore_errors=True)


@pytest.mark.asyncio
async def test_agents_api_endpoints(test_api_client, test_db_session):
    await AgentCapabilityRegistry.initialize_defaults(test_db_session)
    
    # 1. GET /capabilities
    response = await test_api_client.get("/api/v1/agents/capabilities")
    assert response.status_code == 200
    assert len(response.json()) == 7
    assert response.json()[0]["enabled"] is False

    # 2. GET /capabilities/{agent_key}
    response = await test_api_client.get("/api/v1/agents/capabilities/swe_agent")
    assert response.status_code == 200
    assert response.json()["agent_name"] == "SWE-agent"

    # 3. POST /capabilities/{agent_key}/enable
    response = await test_api_client.post("/api/v1/agents/capabilities/swe_agent/enable")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify enable state
    response = await test_api_client.get("/api/v1/agents/capabilities/swe_agent")
    assert response.json()["enabled"] is True

    # 4. POST /capabilities/{agent_key}/disable
    response = await test_api_client.post("/api/v1/agents/capabilities/swe_agent/disable")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify disable state
    response = await test_api_client.get("/api/v1/agents/capabilities/swe_agent")
    assert response.json()["enabled"] is False

    # Enable agent again to test sandbox execution endpoint
    await test_api_client.post("/api/v1/agents/capabilities/swe_agent/enable")

    # 5. POST /runs
    run_payload = {
        "agent_key": "swe_agent",
        "command_handler": "run_tests",
        "arguments": {"test_path": "tests/test_ui_repair_override.py"},
        "target_paths": ["tests/test_ui_repair_override.py"],
        "cost": 0.05,
        "network_domains": []
    }
    response = await test_api_client.post("/api/v1/agents/runs", json=run_payload)
    assert response.status_code == 200
    run_data = response.json()
    assert "run_id" in run_data
    assert run_data["success"] is True

    # 6. GET /runs
    response = await test_api_client.get("/api/v1/agents/runs")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["agent_key"] == "swe_agent"

    # 7. GET /runs/{run_id}
    run_id = run_data["run_id"]
    response = await test_api_client.get(f"/api/v1/agents/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_retry_failed_agent_run_creates_new_sandbox_run(test_api_client, test_db_session):
    await AgentCapabilityRegistry.initialize_defaults(test_db_session)
    await test_api_client.post("/api/v1/agents/capabilities/swe_agent/enable")

    original = AgentRunModel(
        run_id="run-failed-retry-source",
        agent_key="swe_agent",
        status="FAILED",
        input_parameters={
            "handler": "inspect_repo",
            "arguments": {"target_file": "services/ui_repair/service.py"},
            "target_paths": ["services/ui_repair/service.py"],
        },
        sandbox_mode="workspace-write",
        network_policy="disabled",
        cost=0.05,
    )
    test_db_session.add(original)
    await test_db_session.commit()

    response = await test_api_client.post("/api/v1/agents/runs/run-failed-retry-source/retry")
    assert response.status_code == 200
    data = response.json()
    assert data["retried_from_run_id"] == "run-failed-retry-source"
    assert data["run_id"] != "run-failed-retry-source"
    assert data["success"] is True

    stmt = select(AgentRunModel).where(AgentRunModel.run_id == data["run_id"])
    res = await test_db_session.execute(stmt)
    retry_run = res.scalars().first()
    assert retry_run is not None
    assert retry_run.agent_key == "swe_agent"
    assert retry_run.status == "COMPLETED"


@pytest.mark.asyncio
async def test_retry_completed_agent_run_is_rejected(test_api_client, test_db_session):
    await AgentCapabilityRegistry.initialize_defaults(test_db_session)
    completed = AgentRunModel(
        run_id="run-completed-no-retry",
        agent_key="swe_agent",
        status="COMPLETED",
        input_parameters={
            "handler": "inspect_repo",
            "arguments": {"target_file": "services/ui_repair/service.py"},
            "target_paths": ["services/ui_repair/service.py"],
        },
        sandbox_mode="workspace-write",
        network_policy="disabled",
        cost=0.05,
    )
    test_db_session.add(completed)
    await test_db_session.commit()

    response = await test_api_client.post("/api/v1/agents/runs/run-completed-no-retry/retry")
    assert response.status_code == 400
    assert "Only FAILED or BLOCKED" in response.json()["detail"]
