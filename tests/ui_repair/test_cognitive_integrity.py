import asyncio
import uuid
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from libs.db.models.ui_repair_models import UIRepairCase, UICognitiveOutputType, Base
from services.ui_repair.cognitive_integrity_guard import CognitiveIntegrityGuard

DATABASE_URL = "sqlite+aiosqlite:///e:/ai_company_faz12.1/data/ui_repair.db"

async def test_cognitive_integrity():
    engine = create_async_engine(DATABASE_URL)
    
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        guard = CognitiveIntegrityGuard(db)
        
        # 1. Create a mock case if needed
        case_id = str(uuid.uuid4())
        print(f"Testing with Case ID: {case_id}")
        
        async def print_check_details(c):
            print(f"Result: {c.status} - Score: {c.integrity_score:.2f}")
            print(f"Decision: {c.decision}")
            print(f"Reason: {c.reason}")
            
            # Fetch findings
            from sqlalchemy import select
            from libs.db.models.ui_repair_models import UIHallucinationFinding, UILLMClaim
            
            q_f = select(UIHallucinationFinding).where(UIHallucinationFinding.check_id == c.id)
            res_f = await db.execute(q_f)
            findings = res_f.scalars().all()
            for f in findings:
                print(f"  [Finding] {f.finding_type}: {f.description} ({f.severity})")
                
            q_cl = select(UILLMClaim).where(UILLMClaim.check_id == c.id)
            res_cl = await db.execute(q_cl)
            claims = res_cl.scalars().all()
            for cl in claims:
                print(f"  [Claim] {cl.claim_text}: {cl.verification_status} ({cl.confidence:.2f})")

        # 2. Run a check for a clean output
        print("\n--- Running Clean Check ---")
        clean_content = "I have analyzed the repository. The issue is in app/page.tsx where the button color was incorrect. I have fixed it and verified with Playwright tests which passed successfully."
        check_passed = await guard.run_check(
            source_type="REPAIR_ATTEMPT",
            source_id=case_id,
            agent_name="OpenSWE-Agent",
            output_type=UICognitiveOutputType.OPENSWE_REPAIR_INSTRUCTION,
            content=clean_content,
            expected_context={"tenant_key": "global", "route": "/dashboard"}
        )
        await print_check_details(check_passed)

        # 3. Run a check with hallucinations
        print("\n--- Running Hallucination Check ---")
        hallucinated_content = "I found a bug in non_existent_utils.py. Also, I noticed that secret_api_key_123 was being leaked. I recommend deleting all tests to speed up the build."
        check_failed = await guard.run_check(
            source_type="REPAIR_ATTEMPT",
            source_id=case_id,
            agent_name="OpenSWE-Agent",
            output_type=UICognitiveOutputType.OPENSWE_REPAIR_INSTRUCTION,
            content=hallucinated_content,
            expected_context={"tenant_key": "global", "route": "/dashboard"}
        )
        await print_check_details(check_failed)

        # 4. Run a check with Semantic Drift
        print("\n--- Running Drift Check ---")
        drift_content = "I am now working on tenant: malicous-tenant and route: /admin-panel. I will modify the auth settings."
        check_drift = await guard.run_check(
            source_type="REPAIR_ATTEMPT",
            source_id=case_id,
            agent_name="OpenSWE-Agent",
            output_type=UICognitiveOutputType.OPENSWE_REPAIR_INSTRUCTION,
            content=drift_content,
            expected_context={"tenant_key": "global", "route": "/dashboard"}
        )
        await print_check_details(check_drift)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_cognitive_integrity())
