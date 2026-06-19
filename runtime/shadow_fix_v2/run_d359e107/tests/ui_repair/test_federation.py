import pytest
import uuid
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UITenantProfile, UIClusterProfile, UITenantProjectBinding,
    UIPolicyRule, UIRepairCase
)
from libs.db.models.core_models import SovereignEvidence
from services.ui_repair.tenant_registry import TenantRegistry
from services.ui_repair.cluster_registry import ClusterRegistry
from services.ui_repair.federated_policy_resolver import FederatedPolicyResolver
from services.ui_repair.tenant_isolation_guard import TenantIsolationGuard
from services.ui_repair.policy_drift_detector import PolicyDriftDetector
from services.ui_repair.schemas import (
    UITenantProfileCreate, UIClusterProfileCreate, UITenantProjectBindingCreate
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from libs.db.base import Base

@pytest.fixture
async def db_session():
    """In-memory SQLite session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_tenant_creation_and_binding(db_session):
    """Test creating a tenant and binding a project."""
    # 1. Create Tenant
    tenant_data = UITenantProfileCreate(
        tenant_key="ACME_CORP",
        tenant_name="Acme Corporation"
    )
    tenant = await TenantRegistry.create_tenant(db_session, tenant_data)
    assert tenant.tenant_key == "ACME_CORP"

    # 2. Create Cluster
    cluster_data = UIClusterProfileCreate(
        cluster_key="EU_WEST_1",
        cluster_name="Europe West Cluster",
        region="eu-west-1"
    )
    cluster = await ClusterRegistry.create_cluster(db_session, cluster_data)
    assert cluster.cluster_key == "EU_WEST_1"

    # 3. Bind Project
    binding_data = UITenantProjectBindingCreate(
        tenant_key="ACME_CORP",
        cluster_key="EU_WEST_1",
        project_key="ECOMMERCE_WEB"
    )
    binding = await TenantRegistry.bind_project_to_tenant(db_session, binding_data)
    assert binding.project_key == "ECOMMERCE_WEB"

@pytest.mark.asyncio
async def test_policy_federation_hierarchy(db_session):
    """Test 'Most Restrictive Wins' hierarchy."""
    project_key = "HIERARCHY_TEST_PROJ"
    tenant_key = "TEST_TENANT"
    
    # Setup binding
    await TenantRegistry.create_tenant(db_session, UITenantProfileCreate(tenant_key=tenant_key, tenant_name="T"))
    await TenantRegistry.bind_project_to_tenant(db_session, UITenantProjectBindingCreate(
        tenant_key=tenant_key, project_key=project_key
    ))

    # 1. Global Rule: ALLOW stagehand
    global_rule = UIPolicyRule(
        policy_key="AUTO_STAGEHAND",
        scope="GLOBAL",
        enabled=True,
        created_by="TEST_OPERATOR",
        rule_definition_json={"then": {"decision": "ALLOW"}}
    )
    db_session.add(global_rule)

    # 2. Tenant Rule: REQUIRE_APPROVAL stagehand (More restrictive than GLOBAL)
    tenant_rule = UIPolicyRule(
        policy_key="AUTO_STAGEHAND",
        scope="TENANT",
        tenant_key=tenant_key,
        enabled=True,
        created_by="TEST_OPERATOR",
        rule_definition_json={"then": {"decision": "REQUIRE_APPROVAL"}}
    )
    db_session.add(tenant_rule)
    await db_session.commit()

    # 3. Resolve
    resolver = FederatedPolicyResolver(db_session)
    engine = await resolver.get_effective_engine(project_key)
    decision = engine.evaluate("AUTO_STAGEHAND", {"project_key": project_key})
    
    # Should be REQUIRE_APPROVAL (Tenant wins because it's more restrictive)
    assert decision["decision"] == "REQUIRE_APPROVAL"

@pytest.mark.asyncio
async def test_tenant_isolation_violation(db_session):
    """Test that TenantIsolationGuard blocks cross-tenant access."""
    # Setup two tenants
    await TenantRegistry.create_tenant(db_session, UITenantProfileCreate(tenant_key="T1", tenant_name="T1"))
    await TenantRegistry.create_tenant(db_session, UITenantProfileCreate(tenant_key="T2", tenant_name="T2"))
    
    # Create a case for T1
    case = UIRepairCase(
        id=uuid.uuid4(),
        tenant_key="T1",
        project_key="P1",
        route="/dashboard",
        status="OPEN",
        severity="HIGH",
        failure_type="UI_FAIL"
    )
    db_session.add(case)
    await db_session.commit()

    # T2 attempts to access T1's case
    guard = TenantIsolationGuard()
    is_allowed = await guard.validate_resource_access(db_session, "T2", "CASE", case.id)
    
    assert is_allowed is False
    
    # Verify incident was logged
    stmt = select(SovereignEvidence).where(SovereignEvidence.evidence_type == "ISOLATION_VIOLATION")
    evidence = (await db_session.execute(stmt)).scalars().all()
    assert len(evidence) > 0
    assert evidence[0].payload["tenant_key"] == "T2"

@pytest.mark.asyncio
async def test_policy_drift_detection(db_session):
    """Test detection of relaxed local policies."""
    # 1. Global Rule: DENY direct execution
    global_rule = UIPolicyRule(
        policy_key="DIRECT_EXEC",
        scope="GLOBAL",
        enabled=True,
        created_by="TEST_OPERATOR",
        rule_definition_json={"then": {"decision": "DENY"}}
    )
    db_session.add(global_rule)

    # 2. Project Rule: ALLOW direct execution (Relaxed drift!)
    project_rule = UIPolicyRule(
        policy_key="DIRECT_EXEC",
        scope="PROJECT",
        project_key="RELAXED_PROJ",
        tenant_key="T1",
        enabled=True,
        created_by="TEST_OPERATOR",
        rule_definition_json={"then": {"decision": "ALLOW"}}
    )
    db_session.add(project_rule)
    await db_session.commit()

    # 3. Scan
    drifts = await PolicyDriftDetector.scan_for_drifts(db_session)
    assert len(drifts) > 0
    assert drifts[0].drift_type == "RELAXED_RESTRICTION"
    assert drifts[0].project_key == "RELAXED_PROJ"
