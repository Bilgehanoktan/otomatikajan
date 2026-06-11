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
from libs.db.models.repair_models import AgentArtifactPromotionModel, AgentRunModel
from libs.db.models.governance_models import GovernanceProofEventRecord
from services.repair.external_agents.agent_promotion_gate import AgentPromotionGate
from services.repair.external_agents.agent_output_verifier import AgentOutputVerifier

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
    from services.workflow_api.main import app
    
    async def override_get_db():
        yield test_db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    async def override_get_identity():
        return {"id": uuid.uuid4(), "email": "admin@sovereign.agi", "name": "admin", "role": "SOVEREIGN_PRIME", "type": "operator"}
        
    async def override_require_permission():
        return {"id": uuid.uuid4(), "email": "admin@sovereign.agi", "name": "admin", "role": "SOVEREIGN_PRIME", "type": "operator"}

    from services.auth.jwt_auth import get_current_identity, require_permission
    
    app.dependency_overrides[get_current_identity] = override_get_identity
    app.dependency_overrides[require_permission("agents.promotions.read")] = override_require_permission
    app.dependency_overrides[require_permission("agents.promotions.create")] = override_require_permission
    app.dependency_overrides[require_permission("agents.promotions.approve")] = override_require_permission
    app.dependency_overrides[require_permission("agents.promotions.execute")] = override_require_permission
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_promotion_request_creation_and_syntax_verification(test_db_session, tmp_path):
    # 1. Create a syntax-error Python file in sandbox
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def test_broken_syntax(\n  pass\n", encoding="utf-8")
    
    # Creation should trigger synchronous validation
    promo_bad = await AgentPromotionGate.create_promotion_request(
        db=test_db_session,
        run_id="run-1",
        artifact_type="source_file",
        sandbox_artifact_path=str(bad_file),
        target_repo_path="apps/refine_control_plane/src/bad.py",
        created_by="operator@sovereign.agi"
    )
    assert promo_bad.status == "VERIFICATION_FAILED"
    assert "Syntax Error" in promo_bad.verification_details.get("syntax_error", "")
    assert promo_bad.verification_score == 0.0

    # 2. Create a valid Python file in sandbox
    good_file = tmp_path / "good.py"
    good_file.write_text("def test_ok():\n    pass\n", encoding="utf-8")
    
    promo_good = await AgentPromotionGate.create_promotion_request(
        db=test_db_session,
        run_id="run-2",
        artifact_type="source_file",
        sandbox_artifact_path=str(good_file),
        target_repo_path="apps/refine_control_plane/src/good.py",
        created_by="operator@sovereign.agi"
    )
    assert promo_good.status == "PENDING_APPROVAL"
    assert promo_good.verification_score == 1.0

@pytest.mark.asyncio
async def test_target_path_canonical_resolutions(test_db_session, tmp_path):
    sandbox_file = tmp_path / "artifact.py"
    sandbox_file.write_text("print('test')", encoding="utf-8")

    # 1. Blocked path traversal attempt (escaping repository root)
    with pytest.raises(ValueError, match="Path traversal attempt"):
        await AgentPromotionGate.create_promotion_request(
            db=test_db_session,
            run_id="run-traverse",
            artifact_type="source_file",
            sandbox_artifact_path=str(sandbox_file),
            target_repo_path="../../etc/passwd"
        )

    # 2. Blocked path (blocklist check)
    with pytest.raises(ValueError, match="blocked by security policy"):
        await AgentPromotionGate.create_promotion_request(
            db=test_db_session,
            run_id="run-blocklist",
            artifact_type="source_file",
            sandbox_artifact_path=str(sandbox_file),
            target_repo_path="libs/db/session.py"
        )

    # 3. Not in allowlist
    with pytest.raises(ValueError, match="not in the allowed directories list"):
        await AgentPromotionGate.create_promotion_request(
            db=test_db_session,
            run_id="run-allowlist",
            artifact_type="source_file",
            sandbox_artifact_path=str(sandbox_file),
            target_repo_path="services/workflow_api/main.py"
        )

@pytest.mark.asyncio
async def test_promotion_status_state_machine(test_db_session, tmp_path):
    sandbox_file = tmp_path / "valid.py"
    sandbox_file.write_text("a = 1", encoding="utf-8")

    promo = await AgentPromotionGate.create_promotion_request(
        db=test_db_session,
        run_id="run-state",
        artifact_type="source_file",
        sandbox_artifact_path=str(sandbox_file),
        target_repo_path="apps/refine_control_plane/src/valid.py"
    )
    assert promo.status == "PENDING_APPROVAL"

    # Cannot execute directly from PENDING_APPROVAL
    with pytest.raises(ValueError, match="Must be 'APPROVED'"):
        await AgentPromotionGate.execute_promotion(test_db_session, promo.promotion_id, "admin")

    # Approve request
    await AgentPromotionGate.approve_promotion(test_db_session, promo.promotion_id, "admin")
    assert promo.status == "APPROVED"

    # Rejecting an approved or executing request is checked
    # Reject should work
    await AgentPromotionGate.reject_promotion(test_db_session, promo.promotion_id, "admin")
    assert promo.status == "REJECTED"

    # Cannot approve a REJECTED request
    with pytest.raises(ValueError, match="Must be 'PENDING_APPROVAL'"):
        await AgentPromotionGate.approve_promotion(test_db_session, promo.promotion_id, "admin")

@pytest.mark.asyncio
async def test_promotion_execution_hash_mismatch(test_db_session, tmp_path):
    sandbox_file = tmp_path / "hash.py"
    sandbox_file.write_text("val = 123", encoding="utf-8")

    promo = await AgentPromotionGate.create_promotion_request(
        db=test_db_session,
        run_id="run-hash",
        artifact_type="source_file",
        sandbox_artifact_path=str(sandbox_file),
        target_repo_path="apps/refine_control_plane/src/hash.py"
    )
    await AgentPromotionGate.approve_promotion(test_db_session, promo.promotion_id, "admin")

    # Modify the sandbox file after approval to trigger hash mismatch
    sandbox_file.write_text("val = 999", encoding="utf-8")

    success, msg = await AgentPromotionGate.execute_promotion(test_db_session, promo.promotion_id, "admin")
    assert success is False
    assert "Integrity check failed" in msg
    assert promo.status == "PROMOTION_FAILED"

@pytest.mark.asyncio
async def test_promotion_execution_no_direct_mutation_by_default(test_db_session, tmp_path):
    sandbox_file = tmp_path / "safe.py"
    sandbox_file.write_text("safe_val = 1", encoding="utf-8")

    target_rel_path = "apps/refine_control_plane/src/safe.py"

    promo = await AgentPromotionGate.create_promotion_request(
        db=test_db_session,
        run_id="run-safe",
        artifact_type="source_file",
        sandbox_artifact_path=str(sandbox_file),
        target_repo_path=target_rel_path
    )
    await AgentPromotionGate.approve_promotion(test_db_session, promo.promotion_id, "admin")

    # Ensure environment variable is false/unset by default
    if "BILGEAPI_AGENT_PROMOTION_APPLY_TO_REPO" in os.environ:
        del os.environ["BILGEAPI_AGENT_PROMOTION_APPLY_TO_REPO"]

    success, msg = await AgentPromotionGate.execute_promotion(test_db_session, promo.promotion_id, "admin")
    assert success is True
    assert promo.status == "PROMOTED"

    # Main repo must NOT be mutated
    from services.repair.evidence_pack import REPO_ROOT
    main_repo_target = REPO_ROOT / target_rel_path
    assert not main_repo_target.exists()

    # Instead, it must be copied to repair_outputs/promoted_bundles/{promotion_id}/
    bundle_file = REPO_ROOT / "repair_outputs" / "promoted_bundles" / promo.promotion_id / "safe.py"
    assert bundle_file.exists()
    assert bundle_file.read_text(encoding="utf-8") == "safe_val = 1"

    # Clean up bundle directory
    shutil.rmtree(bundle_file.parent.parent, ignore_errors=True)

@pytest.mark.asyncio
async def test_promotion_gate_api_endpoints(test_api_client, test_db_session, tmp_path):
    # Create valid sandbox file
    sandbox_file = tmp_path / "api_test.py"
    sandbox_file.write_text("print('API')", encoding="utf-8")

    # 1. POST /promotions (Create talep)
    payload = {
        "run_id": "run-api-test",
        "artifact_type": "source_file",
        "sandbox_artifact_path": str(sandbox_file),
        "target_repo_path": "apps/refine_control_plane/src/api_test.py"
    }
    response = await test_api_client.post("/api/v1/agents/promotions", json=payload)
    assert response.status_code == 201
    data = response.json()
    promo_id = data["promotion_id"]
    assert data["status"] == "PENDING_APPROVAL"
    assert data["verification_score"] == 1.0

    # 2. GET /promotions (Listeleme)
    response = await test_api_client.get("/api/v1/agents/promotions")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["promotion_id"] == promo_id

    # 3. GET /promotions/{promotion_id} (Detay)
    response = await test_api_client.get(f"/api/v1/agents/promotions/{promo_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "PENDING_APPROVAL"

    # 4. POST /promotions/{promotion_id}/approve (Approve)
    response = await test_api_client.post(f"/api/v1/agents/promotions/{promo_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify approved state
    response = await test_api_client.get(f"/api/v1/agents/promotions/{promo_id}")
    assert response.json()["status"] == "APPROVED"

    # 5. POST /promotions/{promotion_id}/execute (Execute)
    response = await test_api_client.post(f"/api/v1/agents/promotions/{promo_id}/execute")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify promoted state
    response = await test_api_client.get(f"/api/v1/agents/promotions/{promo_id}")
    assert response.json()["status"] == "PROMOTED"

    # Clean up bundle directory created during test
    from services.repair.evidence_pack import REPO_ROOT
    bundle_dir = REPO_ROOT / "repair_outputs" / "promoted_bundles" / promo_id
    shutil.rmtree(bundle_dir.parent, ignore_errors=True)
