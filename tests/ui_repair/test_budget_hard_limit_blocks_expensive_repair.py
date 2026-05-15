import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIBudgetPolicy, UICostEvent
from services.ui_repair.budget_guard import BudgetGuard

@pytest.mark.asyncio
async def test_budget_hard_limit_blocks(db_session: AsyncSession):
    project_key = f"test-project-{uuid.uuid4().hex[:6]}"
    
    # 1. Create a budget policy with $10 hard limit
    policy = UIBudgetPolicy(
        id=uuid.uuid4(),
        project_key=project_key,
        daily_budget_usd=1.0,
        weekly_budget_usd=5.0,
        monthly_budget_usd=10.0,
        hard_limit_usd=10.0,
        soft_limit_percent=80.0,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(policy)
    
    # 2. Add an event that exceeds the limit
    expensive_event = UICostEvent(
        id=uuid.uuid4(),
        project_key=project_key,
        operation_type="OPENSWE_REPAIR",
        estimated_cost_usd=15.0, # Exceeds $10 limit
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(expensive_event)
    await db_session.commit()
    
    # 3. Check budget
    is_allowed, reason, usage = await BudgetGuard.check_budget(db_session, project_key)
    
    assert is_allowed is False
    assert "Hard budget limit exceeded" in reason
    assert usage > 100

@pytest.mark.asyncio
async def test_within_budget_allows(db_session: AsyncSession):
    project_key = f"test-project-{uuid.uuid4().hex[:6]}"
    
    policy = UIBudgetPolicy(
        id=uuid.uuid4(),
        project_key=project_key,
        monthly_budget_usd=100.0,
        hard_limit_usd=150.0,
        soft_limit_percent=80.0,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(policy)
    
    cheap_event = UICostEvent(
        id=uuid.uuid4(),
        project_key=project_key,
        operation_type="MONITORING_RUN",
        estimated_cost_usd=1.0,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(cheap_event)
    await db_session.commit()
    
    is_allowed, reason, usage = await BudgetGuard.check_budget(db_session, project_key)
    
    assert is_allowed is True
    assert usage == 1.0 # 1/100 * 100
