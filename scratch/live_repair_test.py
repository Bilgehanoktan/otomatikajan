
import asyncio
import logging
import uuid
import sys
import os

# Ensure the project root is in the path
sys.path.append(os.getcwd())

from services.repair.ui_repair_orchestrator import UIRepairOrchestrator
from libs.db.session import AsyncSessionLocal
from libs.db.models.repair_models import UIRepairPRReview, UIRepairPRFinding
from sqlalchemy import select, desc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveTest")

async def run_live_validation():
    print("\n--- Starting Phase 32 Live Validation Cycle ---")
    orchestrator = UIRepairOrchestrator()
    
    # We'll use a unique case ID for this test
    test_case_id = f"live-test-{uuid.uuid4().hex[:8]}"
    test_url = "https://app.sovereign-agi.local/dashboard"
    
    print(f"[*] Triggering repair for: {test_url}")
    print(f"[*] Case ID: {test_case_id}")
    
    try:
        # Run the full cycle
        result = await orchestrator.run_full_repair_cycle(test_case_id, test_url)
        
        print("\n[OK] Orchestrator Cycle Finished!")
        print(f"Status: {result.get('final_status')}")
        print(f"PR URL: {result.get('review').pr_url if result.get('review') else 'N/A'}")
        
        # Verify Database Persistence
        print("\n[INFO] Verifying Database Persistence...")
        
        # Note: The orchestrator DOES NOT save to the DB itself, the ROUTER does.
        # But for this live test, we want to simulate the router's behavior or just verify
        # that we COULD save it.
        # Actually, let's manually perform the save logic here to confirm the DB models are working.
        
        async with AsyncSessionLocal() as db:
            review_id = str(uuid.uuid4())
            review_obj = result.get("review")
            
            review = UIRepairPRReview(
                review_id=review_id,
                case_id=test_case_id,
                pr_url=getattr(review_obj, 'pr_url', 'http://error.url') if review_obj else 'http://error.url',
                status=result.get("final_status", "PENDING"),
                summary="LIVE TEST: Verified persistence layer.",
                governance_decision=result.get("final_status", "PENDING")
            )
            db.add(review)
            await db.commit()
            print(f"[OK] Record saved to DB (Review ID: {review_id})")
            
            # Verify it's there
            q = select(UIRepairPRReview).where(UIRepairPRReview.case_id == test_case_id)
            res = await db.execute(q)
            db_record = res.scalars().first()
            
            if db_record:
                print(f"SUCCESS: Verified record in DB with PR URL: {db_record.pr_url}")
            else:
                print("ERROR: Record not found in DB after commit!")
                
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_live_validation())
