import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import UIBudgetPolicy, UICostEvent
from .schemas import UIBudgetPolicyCreate

class BudgetGuard:
    """Enforces financial guardrails and handles budget overrides."""
    
    @staticmethod
    async def get_policy(db: AsyncSession, project_key: str) -> Optional[UIBudgetPolicy]:
        stmt = select(UIBudgetPolicy).where(UIBudgetPolicy.project_key == project_key)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def check_budget(db: AsyncSession, project_key: str) -> Tuple[bool, str, float]:
        """
        Check if project is within budget.
        Returns: (is_allowed, reason, current_usage_percent)
        """
        policy = await BudgetGuard.get_policy(db, project_key)
        if not policy:
            return True, "No budget policy defined", 0.0
            
        # Calculate current monthly spend
        start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.sum(UICostEvent.estimated_cost_usd)).where(
            UICostEvent.project_key == project_key,
            UICostEvent.created_at >= start_of_month
        )
        result = await db.execute(stmt)
        current_spend = result.scalar() or 0.0
        
        usage_percent = (current_spend / policy.monthly_budget_usd) * 100 if policy.monthly_budget_usd > 0 else 0
        
        if current_spend >= policy.hard_limit_usd:
            return False, f"Hard budget limit exceeded: ${current_spend:.2f} / ${policy.hard_limit_usd:.2f}", usage_percent
            
        if usage_percent >= policy.soft_limit_percent:
            return True, f"Soft budget limit reached ({usage_percent:.1f}%)", usage_percent
            
        return True, "Within budget", usage_percent

    @staticmethod
    async def create_or_update_policy(db: AsyncSession, data: UIBudgetPolicyCreate) -> UIBudgetPolicy:
        policy = await BudgetGuard.get_policy(db, data.project_key)
        if policy:
            policy.daily_budget_usd = data.daily_budget_usd
            policy.weekly_budget_usd = data.weekly_budget_usd
            policy.monthly_budget_usd = data.monthly_budget_usd
            policy.hard_limit_usd = data.hard_limit_usd
            policy.soft_limit_percent = data.soft_limit_percent
            policy.action_on_soft_limit = data.action_on_soft_limit
            policy.action_on_hard_limit = data.action_on_hard_limit
            policy.updated_at = datetime.now(timezone.utc)
        else:
            policy = UIBudgetPolicy(
                id=uuid.uuid4(),
                project_key=data.project_key,
                team_key=data.team_key,
                daily_budget_usd=data.daily_budget_usd,
                weekly_budget_usd=data.weekly_budget_usd,
                monthly_budget_usd=data.monthly_budget_usd,
                hard_limit_usd=data.hard_limit_usd,
                soft_limit_percent=data.soft_limit_percent,
                action_on_soft_limit=data.action_on_soft_limit,
                action_on_hard_limit=data.action_on_hard_limit,
                created_at=datetime.now(timezone.utc)
            )
            db.add(policy)
            
        await db.commit()
        await db.refresh(policy)
        return policy
