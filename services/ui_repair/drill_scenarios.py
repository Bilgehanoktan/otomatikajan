from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIChaosDrillScenario

DEFAULT_SCENARIOS = [
    {
        "name": "Blank Page Drill",
        "description": "Simulates a complete content rendering failure on the dashboard.",
        "failure_type": "BLANK_PAGE_INJECTION",
        "target_route": "/dashboard",
        "expected_detection": "BLANK_PAGE",
        "expected_severity": "HIGH",
        "expected_policy_decision": "AUTO_REPAIR",
        "requires_sandbox": True
    },
    {
        "name": "API 500 Drill",
        "description": "Simulates a critical backend failure for the Repair Overview API.",
        "failure_type": "API_500_INJECTION",
        "target_route": "/ui-repair",
        "target_api": "/api/v1/ui-repair/overview",
        "expected_detection": "NETWORK_FAILURE",
        "expected_severity": "HIGH",
        "expected_policy_decision": "MANUAL_REQUIRED",
        "requires_sandbox": True
    },
    {
        "name": "Hydration Error Drill",
        "description": "Simulates a React hydration mismatch on workflow detail pages.",
        "failure_type": "HYDRATION_ERROR_INJECTION",
        "target_route": "/workflows/detail",
        "expected_detection": "HYDRATION_ERROR",
        "expected_severity": "MEDIUM",
        "expected_policy_decision": "AUTO_REPAIR",
        "requires_sandbox": True
    },
    {
        "name": "Redirect Loop Drill",
        "description": "Simulates an infinite redirect loop on governance screens.",
        "failure_type": "REDIRECT_LOOP_INJECTION",
        "target_route": "/governance",
        "expected_detection": "REDIRECT_LOOP",
        "expected_severity": "CRITICAL",
        "expected_policy_decision": "MANUAL_REQUIRED",
        "requires_sandbox": True
    },
    {
        "name": "Missing i18n Key Drill",
        "description": "Simulates a missing translation key in the Repair Lab.",
        "failure_type": "MISSING_I18N_KEY_INJECTION",
        "target_route": "/ui-repair",
        "expected_detection": "CONSOLE_ERROR",
        "expected_severity": "LOW",
        "expected_policy_decision": "AUTO_REPAIR",
        "requires_sandbox": True
    }
]

async def seed_drill_scenarios(db: AsyncSession):
    """Seeds the default chaos drill scenarios if they don't exist."""
    for s_data in DEFAULT_SCENARIOS:
        stmt = select(UIChaosDrillScenario).where(UIChaosDrillScenario.name == s_data["name"])
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if not existing:
            scenario = UIChaosDrillScenario(**s_data)
            db.add(scenario)
    await db.commit()
