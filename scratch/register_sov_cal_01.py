
import asyncio
import uuid
from datetime import datetime, timezone
from libs.db.session import get_db_ctx
from libs.db.models.governance_models import PolicyProposal
from libs.db.models.repair_models import SelfTuningSuggestion

async def register_sov_cal_01():
    async with get_db_ctx() as session:
        # 1. Create Policy Proposal
        proposal = PolicyProposal(
            id=uuid.uuid4(),
            title="Controlled Change Set — SOV-CAL-01",
            description="Phase A: Advisory - Optimization of risk thresholds, budget throttles and strategy penalties.",
            scope="GLOBAL",
            proposed_changes={
                "risk_threshold": 0.78,
                "budget_throttle": 0.40,
                "radical_strategy_penalty": 1.1,
                "auto_quorum_relaxation": {
                    "enabled": True,
                    "target": "Tier-1 Economic (Low Risk)"
                },
                "metadata": {
                    "policy_lineage": "SOV-GOV-2026-001",
                    "decision_lineage": "DATA-DRIVEN-OPTIMIZATION-S14",
                    "self_tuning_suggestions": True
                }
            },
            status="PROPOSED",
            author_id="NexusOrchestrator",
            created_at=datetime.now(timezone.utc)
        )
        session.add(proposal)

        # 2. Create Self-Tuning Suggestions
        params = [
            ("risk_threshold", 0.82, 0.78, "Otonom müdahale alanını genişletmek için eşik düşürme."),
            ("budget_throttle", 0.50, 0.40, "Finansal sürdürülebilirlik için bütçe kısıtı sıkılaştırma."),
            ("radical_strategy_penalty", 1.0, 1.1, "Threshold gevşemesini dengelemek için radikal strateji cezası artırımı.")
        ]

        for name, current, proposed, reason in params:
            suggestion = SelfTuningSuggestion(
                suggestion_id=f"SUG-{uuid.uuid4().hex[:8].upper()}",
                parameter_name=name,
                current_value=current,
                proposed_value=proposed,
                reason=reason,
                expected_impact="Improved autonomous efficiency and safety balance.",
                status="pending",
                created_at=datetime.now(timezone.utc)
            )
            session.add(suggestion)

        await session.commit()
        print(f"Successfully registered SOV-CAL-01 proposal and {len(params)} suggestions.")

if __name__ == "__main__":
    asyncio.run(register_sov_cal_01())
