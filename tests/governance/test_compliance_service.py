
import pytest
from datetime import datetime, timezone, timedelta
from services.compliance.compliance_service import ComplianceService
from libs.db.models.compliance_models import RetentionPolicy, EvidenceSeal

@pytest.mark.asyncio
async def test_compliance_defaults_init():
    await ComplianceService.initialize_defaults()
    
    policy = await ComplianceService.get_retention_policy("TELEMETRY")
    assert policy is not None
    assert policy.hot_retention_days == 90
    
    policy2 = await ComplianceService.get_retention_policy("DECISION_LINEAGE")
    assert policy2.is_permanent is True

@pytest.mark.asyncio
async def test_evidence_sealing():
    import uuid
    record_id = str(uuid.uuid4())
    content = {"decision": "scale_up", "reason": "high_load", "agent": "worker-1"}
    
    hash_val = await ComplianceService.seal_record(
        table_name="test_table",
        record_id=record_id,
        content=content
    )
    
    assert len(hash_val) == 64 # SHA-256
    
    # Verify persistence
    from libs.db.session import get_db, get_db_ctx
    from sqlalchemy import select
    async with get_db_ctx() as session:
        res = await session.execute(select(EvidenceSeal).where(EvidenceSeal.target_id == record_id))
        seal = res.scalar_one()
        assert seal.seal_signature == hash_val
