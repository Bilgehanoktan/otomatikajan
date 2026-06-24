import pytest
from datetime import datetime, timezone
from apps.bilgeapi.repositories.memory import (
    InMemoryIncidentRepository,
    InMemoryDiagnosticRepository,
    InMemoryFindingRepository,
    memory_repositories
)
from apps.bilgeapi.schemas.incident import IncidentCreate, Severity

@pytest.fixture(autouse=True)
def clean_repos():
    memory_repositories.clear_all()

@pytest.mark.asyncio
async def test_tenant_isolation_boundaries():
    incident_repo = InMemoryIncidentRepository()
    
    # 1. Create incident for tenant_A
    inc_a = await incident_repo.create(
        IncidentCreate(
            project_key="proj-a",
            source_system="app",
            environment="production",
            kind="generic",
            severity=Severity.MEDIUM,
            error_message="Error in tenant A",
            occurred_at=datetime.now(timezone.utc),
            correlation_id="corr-a"
        ),
        tenant_id="tenant-A"
    )
    
    # 2. Assert tenant_A can retrieve it
    retrieved_a = await incident_repo.get(inc_a.id, tenant_id="tenant-A")
    assert retrieved_a is not None
    assert retrieved_a.error_message == "Error in tenant A"
    
    # 3. Assert tenant_B gets None (fail-closed/404 behavior, does not leak existence)
    retrieved_b = await incident_repo.get(inc_a.id, tenant_id="tenant-B")
    assert retrieved_b is None
    
    # 4. Assert listing incidents filters by tenant
    list_a = await incident_repo.list_all(tenant_id="tenant-A")
    assert len(list_a) == 1
    assert list_a[0].id == inc_a.id
    
    list_b = await incident_repo.list_all(tenant_id="tenant-B")
    assert len(list_b) == 0

@pytest.mark.asyncio
async def test_bypass_tenant_context():
    incident_repo = InMemoryIncidentRepository()
    
    inc_a = await incident_repo.create(
        IncidentCreate(
            project_key="proj-a",
            source_system="app",
            environment="production",
            kind="generic",
            severity=Severity.MEDIUM,
            error_message="Error in tenant A",
            occurred_at=datetime.now(timezone.utc),
            correlation_id="corr-a"
        ),
        tenant_id="tenant-A"
    )
    
    # Internal system/admin bypass_tenant=True should be able to view cross-tenant objects
    system_view = await incident_repo.get(inc_a.id, tenant_id="tenant-B", bypass_tenant=True)
    assert system_view is not None
    assert system_view.id == inc_a.id

@pytest.mark.asyncio
async def test_missing_tenant_fails_closed():
    incident_repo = InMemoryIncidentRepository()
    
    # Writing without tenant_id or empty string must fail
    with pytest.raises(ValueError):
        await incident_repo.create(
            IncidentCreate(
                project_key="proj-a",
                source_system="app",
                environment="production",
                kind="generic",
                severity=Severity.MEDIUM,
                error_message="Error",
                occurred_at=datetime.now(timezone.utc),
                correlation_id="corr-a"
            ),
            tenant_id=""
        )

@pytest.mark.asyncio
async def test_parameter_shift_compatibility():
    incident_repo = InMemoryIncidentRepository()
    
    inc_a = await incident_repo.create(
        IncidentCreate(
            project_key="proj-a",
            source_system="app",
            environment="production",
            kind="generic",
            severity=Severity.MEDIUM,
            error_message="Error in tenant A",
            occurred_at=datetime.now(timezone.utc),
            correlation_id="corr-a"
        ),
        tenant_id="tenant-A"
    )
    
    # Legacy parameter style: get(id, True) where True is bypass_tenant passed to tenant_id
    # Parameter shift logic should detect True (bool) in tenant_id position, swap it to bypass_tenant, and default tenant_id to "default"
    # Note: Since the incident is created with "tenant-A", bypass_tenant=True will allow getting it.
    retrieved_legacy = await incident_repo.get(inc_a.id, True)
    assert retrieved_legacy is not None
    assert retrieved_legacy.id == inc_a.id
