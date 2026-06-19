import os
import uuid
import pytest
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from libs.db.models import Base
from libs.db.session import get_db
from libs.db.models.repair_models import AgentCapabilityModel, AgentArtifactPromotionModel, AgentRunModel
from services.repair.external_agents.agent_policy_simulator import AgentPolicySimulator
from services.repair.external_agents.agent_promotion_gate import AgentPromotionGate

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
        # Seed test capability
        cap = AgentCapabilityModel(
            agent_key="test_agent",
            agent_name="Test Agent",
            description="Testing capability",
            enabled=True,
            risk_level="MEDIUM",
            sandbox_mode="workspace-write",
            max_cost_limit=5.0,
            requires_human_approval=True,
            network_policy="disabled",
            allowed_domains=[],
            allowed_directories=["apps/refine_control_plane/src/**"],
            blocked_directories=[".env"],
            allowed_commands=[],
            blocked_commands=[]
        )
        session.add(cap)
        await session.commit()
        yield session
        await session.rollback()

@pytest.fixture
async def test_api_client(test_db_session):
    from services.workflow_api.main import app
    
    async def override_get_db():
        yield test_db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    async def override_require_permission():
        return {"id": uuid.uuid4(), "email": "operator@sovereign.agi", "role": "OPERATOR", "type": "operator"}

    from services.auth.jwt_auth import get_current_identity, require_permission
    
    app.dependency_overrides[get_current_identity] = override_require_permission
    app.dependency_overrides[require_permission("agents.read")] = override_require_permission
    app.dependency_overrides[require_permission("agents.manage")] = override_require_permission
    app.dependency_overrides[require_permission("agents.promotions.execute")] = override_require_permission
    app.dependency_overrides[require_permission("agents.promotions.approve")] = override_require_permission
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_risk_score_calculation():
    # LOW risk
    score_low, reasons_low = AgentPolicySimulator.calculate_risk_score(
        agent_enabled=True, sandbox_mode="read-only", path_check=(True, ""),
        cost=0.01, cost_limit=1.0, network_request=False, network_allowed="disabled"
    )
    assert score_low == 5.0  # read-only cost risk
    assert AgentPolicySimulator.get_risk_level(score_low) == "LOW"
    assert AgentPolicySimulator.get_decision(AgentPolicySimulator.get_risk_level(score_low)) == "ALLOW"

    # CRITICAL risk
    score_crit, reasons_crit = AgentPolicySimulator.calculate_risk_score(
        agent_enabled=True, sandbox_mode="direct-write", path_check=(False, "Path traversal"),
        cost=1.5, cost_limit=1.0, network_request=True, network_allowed="disabled",
        hash_mismatch=True
    )
    assert score_crit == 100.0
    assert AgentPolicySimulator.get_risk_level(score_crit) == "CRITICAL"
    assert AgentPolicySimulator.get_decision(AgentPolicySimulator.get_risk_level(score_crit)) == "BLOCK"

@pytest.mark.asyncio
async def test_simulate_agent_run(test_db_session):
    # Valid allowed path
    res = await AgentPolicySimulator.simulate_agent_run(
        db=test_db_session,
        agent_key="test_agent",
        action_type="run_patch",
        target_paths=["apps/refine_control_plane/src/App.tsx"],
        cost=0.1,
        network_request=False
    )
    assert res["decision"] in ["ALLOW", "HUMAN_GATE_REQUIRED"]
    assert len(res["reasons"]) > 0

    # Path traversal block
    res_block = await AgentPolicySimulator.simulate_agent_run(
        db=test_db_session,
        agent_key="test_agent",
        action_type="run_patch",
        target_paths=["../../etc/passwd"],
        cost=0.1,
        network_request=False
    )
    assert res_block["decision"] == "BLOCK"
    assert any("Path traversal" in r for r in res_block["reasons"])

@pytest.mark.asyncio
async def test_simulate_promotion_and_execute_gating(test_db_session, tmp_path):
    sandbox_file = tmp_path / "valid.py"
    sandbox_file.write_text("print('test')", encoding="utf-8")

    # Create promotion request
    promo = await AgentPromotionGate.create_promotion_request(
        db=test_db_session,
        run_id="run-sim",
        artifact_type="source_file",
        sandbox_artifact_path=str(sandbox_file),
        target_repo_path="apps/refine_control_plane/src/valid.py"
    )
    await AgentPromotionGate.approve_promotion(test_db_session, promo.promotion_id, "operator@sovereign.agi")

    # 1. Direct execution should FAIL because simulate_promotion hasn't run
    with pytest.raises(ValueError, match="simulate_promotion result is required"):
        await AgentPromotionGate.execute_promotion(test_db_session, promo.promotion_id, "operator@sovereign.agi")

    # 2. Run simulation
    sim_res = await AgentPolicySimulator.simulate_promotion(test_db_session, promo.promotion_id)
    assert sim_res["decision"] == "ALLOW"
    assert "simulation_result_hash" in sim_res

    # Store simulation hash (simulate-promotion endpoint behavior)
    promo.verification_details["simulation_result"] = sim_res
    promo.verification_details["simulation_result_hash"] = sim_res["simulation_result_hash"]
    await test_db_session.commit()

    # 3. Execution should succeed now (Isolated workspace bundle promotion by default)
    if "BILGEAPI_AGENT_PROMOTION_APPLY_TO_REPO" in os.environ:
        del os.environ["BILGEAPI_AGENT_PROMOTION_APPLY_TO_REPO"]
        
    success, msg = await AgentPromotionGate.execute_promotion(test_db_session, promo.promotion_id, "operator@sovereign.agi")
    assert success is True
    assert promo.status == "PROMOTED"

@pytest.mark.asyncio
async def test_simulation_endpoints_via_api(test_api_client, test_db_session, tmp_path):
    # 1. POST /policy/simulate-run
    payload_run = {
        "agent_key": "test_agent",
        "action_type": "run_patch",
        "target_paths": ["apps/refine_control_plane/src/App.tsx"],
        "cost": 0.05,
        "network_request": False
    }
    response = await test_api_client.post("/api/v1/agents/policy/simulate-run", json=payload_run)
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "risk_score" in data

    # Create promo request for simulate-promotion
    sandbox_file = tmp_path / "api_sim.py"
    sandbox_file.write_text("x = 1", encoding="utf-8")
    
    promo = await AgentPromotionGate.create_promotion_request(
        db=test_db_session,
        run_id="run-api-sim",
        artifact_type="source_file",
        sandbox_artifact_path=str(sandbox_file),
        target_repo_path="apps/refine_control_plane/src/api_sim.py"
    )

    # 2. POST /policy/simulate-promotion
    response_promo = await test_api_client.post(
        "/api/v1/agents/policy/simulate-promotion",
        json={"promotion_id": promo.promotion_id}
    )
    assert response_promo.status_code == 200
    data_promo = response_promo.json()
    assert data_promo["decision"] == "ALLOW"
    assert "simulation_result_hash" in data_promo

    # Verify database was updated with simulation result
    await test_db_session.refresh(promo)
    assert promo.verification_details.get("simulation_result_hash") == data_promo["simulation_result_hash"]

    # 3. GET /policy/rules
    response_rules = await test_api_client.get("/api/v1/agents/policy/rules")
    assert response_rules.status_code == 200
    data_rules = response_rules.json()
    assert "allowlist_patterns" in data_rules
    assert "blocklist_patterns" in data_rules
