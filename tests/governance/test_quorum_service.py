
import pytest
from services.governance.quorum_service import QuorumService
from libs.db.models.governance_models import SignoffStatus

@pytest.mark.asyncio
async def test_quorum_requirement_registration():
    req = await QuorumService.register_quorum_requirement(
        component="test_component",
        risk="HIGH",
        count=2,
        desc="Test requirement"
    )
    assert req.required_quorum == 2
    
    # Update
    req2 = await QuorumService.register_quorum_requirement(
        component="test_component",
        risk="HIGH",
        count=3
    )
    assert req2.required_quorum == 3

@pytest.mark.asyncio
async def test_quorum_signoff_logic():
    # 1. Setup requirement
    await QuorumService.register_quorum_requirement("critical_policy", "HIGH", 2)
    
    # 2. Create a main signoff in DB manually or via service (if exists)
    from libs.db.session import get_db, get_db_ctx
    from libs.db.models.governance_models import ProductionSignoff
    import uuid
    
    signoff_id = uuid.uuid4()
    async with get_db_ctx() as session:
        main = ProductionSignoff(
            id=signoff_id,
            component_name="critical_policy",
            version="1.0.0",
            status=SignoffStatus.PENDING
        )
        session.add(main)
        await session.commit()
        
    # 3. Add first signoff
    await QuorumService.add_signoff(str(signoff_id), "operator_1", "Looks good")
    
    async with get_db_ctx() as session:
        from sqlalchemy import select
        res = await session.execute(select(ProductionSignoff).where(ProductionSignoff.id == signoff_id))
        main = res.scalar_one()
        assert main.status == SignoffStatus.PENDING # Still pending (needs 2)
        
    # 4. Add second signoff
    await QuorumService.add_signoff(str(signoff_id), "operator_2", "Approved")
    
    async with get_db_ctx() as session:
        res = await session.execute(select(ProductionSignoff).where(ProductionSignoff.id == signoff_id))
        main = res.scalar_one()
        assert main.status == SignoffStatus.SIGNED # Now signed!
