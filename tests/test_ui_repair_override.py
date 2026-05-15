import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from services.ui_repair.service import UIRepairService
from services.ui_repair.schemas import UIAutonomousOverrideCreate

@pytest.mark.asyncio
async def test_override_requires_rationale():
    db = AsyncMock()
    service = UIRepairService(db)
    
    # Missing rationale should fail (Pydantic validation normally handles this, but we test logic here)
    with pytest.raises(Exception):
        await service.create_autonomous_override(UIAutonomousOverrideCreate(
            action_type="TEST",
            target_type="UI_ROUTE",
            target_id="login",
            blocked_policy_key="BLOCK_ALL",
            override_reason="", # EMPTY
            operator="admin",
            risk_level="HIGH"
        ))

    # Valid override
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    
    override_data = UIAutonomousOverrideCreate(
        action_type="TEST",
        target_type="UI_ROUTE",
        target_id="login",
        blocked_policy_key="BLOCK_ALL",
        override_reason="Critical emergency bypass for hotfix",
        operator="admin",
        risk_level="HIGH"
    )
    
    res = await service.create_autonomous_override(override_data)
    assert res is not None
    db.add.assert_called_once()
    db.commit.assert_called_once()
