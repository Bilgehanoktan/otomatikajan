
import pytest
from datetime import datetime, timezone, timedelta
from services.compliance.compliance_service import ComplianceService
from libs.db.models.compliance_models import AuditBundle

@pytest.mark.asyncio
async def test_audit_bundle_creation():
    start = datetime.now(timezone.utc) - timedelta(days=7)
    end = datetime.now(timezone.utc)
    
    bundle = await ComplianceService.create_audit_bundle(
        name="Q2_2026_Audit",
        start=start,
        end=end,
        creator="admin_operator"
    )
    
    assert bundle.bundle_name == "Q2_2026_Audit"
    assert bundle.integrity_hash == "SEALED"
    
    # Verify in DB
    from libs.db.session import get_db, get_db_ctx
    from sqlalchemy import select
    async with get_db_ctx() as session:
        res = await session.execute(select(AuditBundle).where(AuditBundle.id == bundle.id))
        db_bundle = res.scalar_one()
        assert db_bundle.created_by == "admin_operator"
