import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIAutoPatchExecution, UIPatchCandidate, UIRepairSeverity
)

class PatchCandidatePlanner:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def plan_candidates(self, execution: UIAutoPatchExecution) -> List[UIPatchCandidate]:
        """
        Generates multiple fix strategies based on the incident context.
        """
        strategies = [
            {
                "key": "minimal_safe_fix",
                "strategy": "MINIMAL",
                "summary": "Focuses only on the immediate logic error with minimal side effects.",
                "risk": "LOW"
            },
            {
                "key": "defensive_guard_fix",
                "strategy": "DEFENSIVE",
                "summary": "Adds additional runtime guards and boundary checks around the fix.",
                "risk": "LOW"
            },
            {
                "key": "config_policy_fix",
                "strategy": "POLICY",
                "summary": "Fixes the issue by adjusting policy-as-code configuration.",
                "risk": "MEDIUM"
            }
        ]

        # For critical items, only suggest low-risk minimal fixes by default
        if execution.risk_level == UIRepairSeverity.CRITICAL:
            strategies = [s for s in strategies if s["risk"] == "LOW"]

        candidates = []
        for s in strategies:
            candidate = UIPatchCandidate(
                execution_id=execution.id,
                candidate_key=f"{execution.execution_key}_{s['key']}",
                strategy=s["strategy"],
                summary=s["summary"],
                risk_level=s["risk"],
                affected_files_json=[], # To be populated by file analyzer
                affected_routes_json=[]
            )
            self.db.add(candidate)
            candidates.append(candidate)
        
        await self.db.commit()
        return candidates
