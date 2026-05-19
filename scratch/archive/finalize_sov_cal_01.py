
import asyncio
from libs.db.session import get_db_ctx
from libs.db.models.governance_models import PolicyProposal
from libs.db.models.repair_models import SelfTuningSuggestion
from sqlalchemy import select, update
from datetime import datetime, timezone

async def finalize_sov_cal_01():
    async with get_db_ctx() as session:
        # 1. Update Policy Proposal to APPROVED
        # We find the one with the correct title
        stmt = select(PolicyProposal).where(PolicyProposal.title == "Controlled Change Set — SOV-CAL-01")
        result = await session.execute(stmt)
        proposal = result.scalar_one_or_none()
        
        if proposal:
            proposal.status = "APPROVED"
            proposal.description += f" | PROMOTED on {datetime.now(timezone.utc).isoformat()}"
            print(f"Propsoal {proposal.id} updated to APPROVED.")
        else:
            print("SOV-CAL-01 proposal not found in DB.")

        # 2. Update Self-Tuning Suggestions
        # These are usually indexed by parameter names
        params = ["risk_threshold", "budget_throttle", "radical_strategy_penalty"]
        for param in params:
            stmt = select(SelfTuningSuggestion).where(SelfTuningSuggestion.parameter_name == param)
            results = await session.execute(stmt)
            for suggestion in results.scalars().all():
                suggestion.status = "applied"
                print(f"Suggestion for {param} marked as applied.")

        await session.commit()
        print("--- Finalized Governance Records for SOV-CAL-01 ---")

if __name__ == "__main__":
    asyncio.run(finalize_sov_cal_01())
