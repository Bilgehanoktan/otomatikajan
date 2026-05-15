import pytest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UICostEvent
from services.ui_repair.cost_anomaly_detector import CostAnomalyDetector

@pytest.mark.asyncio
async def test_detect_cost_spike(db_session: AsyncSession):
    project_key = f"anomaly-test-{uuid.uuid4().hex[:6]}"
    now = datetime.now(timezone.utc)
    
    # 1. Create baseline (avg $1/day for 7 days)
    for i in range(2, 9):
        event = UICostEvent(
            id=uuid.uuid4(),
            project_key=project_key,
            estimated_cost_usd=1.0,
            created_at=now - timedelta(days=i)
        )
        db_session.add(event)
    
    # 2. Create spike today ($20)
    spike = UICostEvent(
        id=uuid.uuid4(),
        project_key=project_key,
        estimated_cost_usd=20.0,
        created_at=now - timedelta(hours=2)
    )
    db_session.add(spike)
    await db_session.commit()
    
    # 3. Detect
    anomalies = await CostAnomalyDetector.detect_anomalies(db_session, project_key)
    
    assert len(anomalies) > 0
    assert anomalies[0].anomaly_type == "COST_SPIKE"
    assert anomalies[0].observed_cost_usd == 20.0
    assert anomalies[0].expected_cost_usd == 1.0
    assert anomalies[0].deviation_percent == 1900.0
