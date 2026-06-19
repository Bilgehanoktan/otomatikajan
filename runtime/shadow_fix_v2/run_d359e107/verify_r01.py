import asyncio
import uuid
from libs.db.session import session_scope, init_db
from libs.db.models.core_models import SovereignEvidence
from services.govern.reporting_service import OperationalTrustReport

async def verify_evidence_system():
    print("--- Verifying SovereignEvidence System ---")
    try:
        # 0. Initialize DB (handles SQLite fallback)
        print("Initializing Database...")
        await init_db()
        
        async with session_scope() as db:
            # 1. Create dummy evidence
            evidence = SovereignEvidence(
                evidence_type="test_verification",
                severity="info",
                payload={"msg": "Protocol R-01 Live Verification Test"},
                provenance_hash="sha256:test_hash_123"
            )
            db.add(evidence)
            print("Adding record...")
            await db.commit()
            print("Record committed.")

        # 2. Generate Report
        print("Generating Trust Report...")
        report = await OperationalTrustReport.generate_trust_summary()
        print(f"Total Evidence Points: {report['total_evidence_points']}")
        print(f"Reliability Stats: {report['autonomous_reliability']}")
        
        if report['total_evidence_points'] > 0:
            print("[SUCCESS] R-01 Infrastructure is functional and auditable.")
        else:
            print("[FAILURE] R-01 Infrastructure failed to record/fetch data.")

    except Exception as e:
        print(f"[ERROR] Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_evidence_system())
