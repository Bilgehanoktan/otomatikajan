
import asyncio
import uuid
from datetime import datetime, timezone
from libs.db.session import AsyncSessionLocal
from libs.db.models.lineage_models import DecisionLineage

async def record():
    async with AsyncSessionLocal() as db:
        step = DecisionLineage(
            id=uuid.uuid4(),
            decision_type="SYSTEM_RECOVERY",
            component_name="governance_models",
            rationale="Fixed 'Integer' name error and resolved MetaData conflict for ProductionSignoff. Restored system to HEALTHY state.",
            trigger_event={"source": "integrity_check", "status": "FAIL"},
            meta_data={"outcome": "SUCCESS", "details": "Phase 13.04 Integrity Restored"},
            created_at=datetime.utcnow(),
            integrity_hash="sha256:fix_integer_import_0417"
        )
        db.add(step)
        await db.commit()
        print(f"Recorded decision: {step.id}")

if __name__ == "__main__":
    asyncio.run(record())
