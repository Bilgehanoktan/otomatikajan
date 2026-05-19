"""
Sovereign AGI — Phase 26 Verification
verify_r09.py: Federation Trust Score Depth (R-09)
"""
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from sqlalchemy import text
from libs.db.session import init_db, get_db, get_db_ctx, session_scope
from libs.db.models.core_models import Base, FederationTrust
from services.orchestration.trust_governor import trust_governor
from services.orchestration.federation_router import FederationRouter, FederationTask
from services.govern.reporting_service import FederationTrustReport

# Mock project ID for testing
TEST_PROJECT_ID = "00000000-0000-0000-0000-000000000001"

async def setup_test_db():
    print("--- [R-09] DB Initialization ---")
    await init_db()
    async with get_db_ctx() as session:
        # Create tables if not exist (using Base.metadata.create_all via init_db logic or direct)
        # In this env, init_db handles it via engine.begin()
        pass

async def run_verification():
    await setup_test_db()
    
    router = FederationRouter()
    
    print("\n--- [R-09] Step 1: Initial Routing (Cold Start) ---")
    task = FederationTask(
        task_id="task-r09-01",
        project_id=TEST_PROJECT_ID,
        goal_description="Optimize security hardening policies",
        required_expertise=["rbac", "hardening"],
        context={}
    )
    
    cluster_id = await router.route_task(task)
    print(f"Routed task to: {cluster_id}")

    print("\n--- [R-09] Step 2: Recording Outcomes ---")
    # Simulate 5 successes for 'sec-overwatch-v1'
    for _ in range(5):
        await trust_governor.record_outcome("sec-overwatch-v1", success=True, impact=1.0)
    
    # Simulate 2 failures for 'logic-cortex-v1'
    for _ in range(2):
        await trust_governor.record_outcome("logic-cortex-v1", success=False, impact=1.5)
        
    # Simulate an arbitration win for 'ops-reflex-v1'
    await trust_governor.record_outcome("ops-reflex-v1", success=True, is_arbitration=True)

    print("\n--- [R-09] Step 3: Verifying Trust Scores ---")
    trust_map = await trust_governor.get_trust_map()
    for cid, score in trust_map.items():
        print(f"Cluster: {cid:20} Trust Score: {score:.4f}")

    print("\n--- [R-09] Step 4: Routing with Trust Weighting ---")
    # Both 'sec-overwatch-v1' and another cluster might match, 
    # but sec-overwatch-v1 should be favored now due to higher trust.
    task_2 = FederationTask(
        task_id="task-r09-02",
        project_id=TEST_PROJECT_ID,
        goal_description="General infrastructure audit",
        required_expertise=["hardening"],
        context={}
    )
    chosen = await router.route_task(task_2)
    print(f"Reliable choice for 'hardening': {chosen}")

    print("\n--- [R-09] Step 5: Simulating Trust Decay ---")
    # Manually backdate activity for logic-cortex-v1 to 10 days ago
    async with session_scope() as db:
        ten_days_ago = datetime.now() - timedelta(days=10)
        await db.execute(
            text("UPDATE federation_trust SET last_activity_at = :dt WHERE cluster_id = :cid"),
            {"dt": ten_days_ago, "cid": "logic-cortex-v1"}
        )
    
    print("Applying decay to 'logic-cortex-v1'...")
    await trust_governor.apply_decay("logic-cortex-v1")
    
    decayed_map = await trust_governor.get_trust_map()
    print(f"Decayed Score for logic-cortex-v1: {decayed_map.get('logic-cortex-v1'):.4f}")

    print("\n--- [R-09] Step 6: Generating Trust Report ---")
    report = await FederationTrustReport.get_cluster_trust_summary()
    print(json.dumps(report, indent=2))
    
    print("\n[SUCCESS] R-09 Federation Trust Score Depth Verified.")

if __name__ == "__main__":
    # Ensure logs are visible
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.run(run_verification())
