import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.routers.auth.jwt_auth import auth_service
from packages.persistence.session import AsyncSessionLocal
from sqlalchemy import select
from packages.persistence.models import User

client = TestClient(app)

@pytest.fixture
async def admin_token():
    """Gerçek bir admin token'ı oluşturur."""
    async with AsyncSessionLocal() as db:
        # 1. Admin kullanıcısı var mı kontrol et
        stmt = select(User).where(User.email == "verify@system.local")
        user = (await db.execute(stmt)).scalar_one_or_none()
        
        if not user:
            # 2. Yoksa oluştur (is_admin=True)
            user = await auth_service.register(db, "verify@system.local", "verify_pass_12345678")
            user.is_admin = True
            await db.commit()
        
        # 3. Login ol
        res = await auth_service.login(db, "verify@system.local", "verify_pass_12345678")
        return res.access_token

@pytest.mark.asyncio
async def test_verify_capabilities_endpoint_via_client(admin_token):
    """
    Faz 12.1 Verification: Ensure the /tasks/capabilities endpoint works and
    correctly loads capabilities via agency_loader with REAL JWT auth.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/tasks/capabilities", headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Error: {response.text}"
    data = response.json()
    
    assert "capabilities" in data, "Capabilities key missing from response"
    assert isinstance(data["capabilities"], list), "Capabilities should be a list"
    assert len(data["capabilities"]) > 0, "At least one specialist should be returned"
    assert data.get("source_of_truth") == "agency_loader"


@pytest.mark.asyncio
async def test_sovereign_auditor_check():
    """
    Faz 12.1 Verification: Test the core auditor engine behavior directly.
    """
    from packages.orchestration.agi.cognitive.sovereign_auditor import sovereign_auditor
    
    findings = await sovereign_auditor.run_full_audit()
    assert isinstance(findings, list), "Findings should be a list"
    # Even if there are no findings, the fact that run_full_audit ran without error is a success constraint.

def test_sovereign_evolution_engine_ready():
    """
    Faz 12.1 Verification: Ensure the Evolution Engine instance is correctly loaded.
    """
    try:
        from packages.orchestration.agi.cognitive.evolution_engine import evolution_engine
        assert evolution_engine is not None, "Evolution engine instance should not be None"
    except ImportError as e:
        pytest.fail(f"Evolution engine imports failed: {e}")
