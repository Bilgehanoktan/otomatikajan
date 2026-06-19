import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from services.ui_repair.scheduled_smoke_runner import ScheduledSmokeRunner
from libs.db.models.ui_repair_models import UIMonitoringConfig

@pytest.mark.asyncio
async def test_scheduled_smoke_runner_cycle(db_session):
    # 1. Setup config in database
    config = UIMonitoringConfig(
        id=uuid4(),
        enabled=True,
        auto_repair_enabled=True,
        auto_repair_risk_threshold=0.8,
        max_repairs_per_hour=5,
        max_repairs_per_day=10,
        route_scope_json=[]
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    # 2. Instantiate Runner
    runner = ScheduledSmokeRunner(db_session)

    # 3. Mock `run_smoke_test` in the underlying repair service
    mock_smoke_results = [
        {
            "route": "/",
            "status": "PASS",
            "http_status": 200,
            "response_time_ms": 120.0
        },
        {
            "route": "/repair-lab",
            "status": "FAIL",
            "http_status": 500,
            "response_time_ms": 450.0,
            "console_errors": ["Hydration failed"],
            "network_errors": []
        }
    ]
    
    with patch.object(runner.repair_service.runner, "run_smoke_test", new_callable=AsyncMock) as mock_smoke:
        mock_smoke.return_value = mock_smoke_results
        
        # Mock failure handling in repair_service
        runner.repair_service._handle_failure = AsyncMock(return_value=True) # returns is_new=True
        
        # Act
        result = await runner.run_monitoring_cycle(triggered_by="TEST_CYCLE")
        
        # Assert
        assert result["passed"] == 1
        assert result["failed"] == 1
        assert result["auto_repairs"] == 0 # no auto repair triggered since no actual case was added to mock DB
        assert mock_smoke.called
