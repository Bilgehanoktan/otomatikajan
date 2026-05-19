
import asyncio
from libs.db.session import init_db, session_scope
from libs.db.models.lineage_models import DecisionLineage
from datetime import datetime, timezone
import uuid

async def mock_evolution():
    await init_db()
    async with session_scope() as session:
        lineage = DecisionLineage(
            id=uuid.uuid4(),
            decision_type="SYSTEM_EVOLUTION",
            component_name="libs.workflow.engine",
            rationale="Autonomous Growth Pulse | Optimization of retry logic based on Lab results.",
            trigger_event={"source": "evolution_loop", "case": "re-001"},
            meta_data={"success": True, "risk_level": "low"},
            created_at=datetime.now(timezone.utc)
        )
        session.add(lineage)
        print(f"Mock Evolution entry created: {lineage.id}")

if __name__ == "__main__":
    asyncio.run(mock_evolution())
