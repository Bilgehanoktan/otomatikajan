import asyncio
import uuid
from sqlalchemy import select
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import OperationalIncident
from libs.db.models.learning_models import LearningRecord, ErrorFingerprint
from services.governance.learning_orchestrator import LearningOrchestrator

async def test_learning_flow():
    print("--- Starting Learning Flow Test ---")
    
    async with AsyncSessionLocal() as db:
        # 1. Create a fresh Incident
        incident_id = str(uuid.uuid4())
        new_inc = OperationalIncident(
            id=incident_id,
            incident_type="TEST_NETWORK_TIMEOUT",
            severity="medium",
            message="Connection timeout while fetching node status",
            status="pending"
        )
        db.add(new_inc)
        await db.commit()
        print(f"Created Test Incident: {incident_id}")

        # 2. Simulate Manual Resolution with Learning Integration
        # We'll call the logic directly to verify the service
        print("Simulating resolution and learning record creation...")
        await LearningOrchestrator.record_incident_learning(
            incident_data={
                "id": incident_id,
                "incident_type": "TEST_NETWORK_TIMEOUT",
                "severity": "medium",
                "message": "Connection timeout while fetching node status",
                "component": "NetworkMonitor"
            },
            outcome_data={
                "final_outcome": "SUCCESS",
                "root_cause": "TRANS_LAYER_CONGESTION",
                "operator_override": True,
                "strategy_used": "OPERATOR_TIMEOUT_ADJUSTMENT",
                "repair_latency_s": 45.5
            },
            db=db
        )
        await db.commit()
        print("Learning record created via service.")

        # 3. Verify Database Records
        # Check Fingerprint
        fp_res = await db.execute(select(ErrorFingerprint).where(ErrorFingerprint.component == "NetworkMonitor"))
        fp = fp_res.scalar_one_or_none()
        if fp:
            print(f"Verified Fingerprint: ID={fp.id}, Family={fp.error_family}, Count={fp.recurrence_count}")
        else:
            print("FAILED: Fingerprint not found!")

        # Check Learning Record
        lr_res = await db.execute(select(LearningRecord).where(LearningRecord.incident_id == incident_id))
        lr = lr_res.scalar_one_or_none()
        if lr:
            print(f"Verified Learning Record: ID={lr.id}, Strategy={lr.strategy_used}, Latency={lr.repair_latency_s}")
        else:
            print("FAILED: Learning Record not found!")

    print("--- Test Completed ---")

if __name__ == "__main__":
    asyncio.run(test_learning_flow())
