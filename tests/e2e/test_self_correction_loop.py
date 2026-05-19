import asyncio
import uuid
import os
import sys
from pathlib import Path

# Force TEST environment and SQLite for deterministic E2E testing
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./runtime/data/cortex_local.db"

# Add project root to sys.path
root = Path(os.getcwd()).resolve()
if str(root) not in sys.path:
    sys.path.append(str(root))

from datetime import datetime, timezone
from libs.db.session import get_db, get_db_ctx, init_db
from libs.db.models.core_models import Project, OperationalIncident, SystemImprovement
from libs.db.repositories.repository import ProjectRepository, OperationalIncidentRepository
from workers.workflow_worker.tasks.project_tasks import auto_fix_incident_task, verify_canary_health_task

async def test_self_correction_flow():
    print("\n[PHASE 16 E2E] Starting Self-Correction Loop Test...")
    await init_db()
    
    async with get_db_ctx() as session:
        # 1. Pilot Proje Oluştur
        pilot_project = await ProjectRepository.create(
            db=session,
            title="Self-Correction Pilot",
            description="Testing Incident-to-Patch Loop",
            is_pilot=True
        )
        print(f"OK: Created Pilot Project: {pilot_project.id}")
        await session.commit()

        # 2. Sahte bir olay (incident) oluştur
        dummy_file = "libs/utils/math_helper.py"
        os.makedirs("libs/utils", exist_ok=True)
        with open(dummy_file, "w") as f:
            f.write("def add(a, b):\n    return a + b\n\ndef divide(a, b):\n    # Bug: division by zero not handled properly\n    return a / b\n")
        
        print(f"OK: Created dummy file with bug: {dummy_file}")

        try:
            incident_msg = "ZeroDivisionError: division by zero in libs/utils/math_helper.py:6"
            incident = await OperationalIncidentRepository.create(
                db=session,
                project_id=pilot_project.id,
                incident_type="api_exception",
                message=incident_msg,
                severity="high",
                payload={"stack_trace": "  File \"libs/utils/math_helper.py\", line 6, in divide\n    return a / b\nZeroDivisionError: division by zero"}
            )
            await session.commit()
            print(f"OK: Created Incident: {incident.id}")

            # 3. auto_fix_incident_task'ı doğrudan çağır
            # Not: Ağ kısıtlamaları nedeniyle ModelOrchestrator'ı mock'luyoruz
            print("Action: Mocking ModelOrchestrator for autonomous diagnosis...")
            from unittest.mock import patch, MagicMock
            from libs.llm.model_orchestrator import LLMResponse

            mock_response = LLMResponse(
                content="""
{
  "diagnosis": "The divide function in libs/utils/math_helper.py does not check if the divisor 'b' is zero before performing division, leading to a ZeroDivisionError.",
  "relevant_files": ["libs/utils/math_helper.py"],
  "suggested_patch": "def divide(a, b):\\n    if b == 0:\\n        return 0 # Or raise a custom error\\n    return a / b",
  "confidence_score": 0.95,
  "risk_assessment": "low"
}
""",
                input_tokens=100,
                output_tokens=150,
                model_name="mock-model",
                provider="mock-provider",
                latency_s=0.5,
                cost_usd=0.001
            )

            with patch("libs.llm.model_orchestrator.ModelOrchestrator.complete_task", return_value=mock_response):
                print("Action: Triggering auto_fix_incident_task (Mocked LLM)...")
                result = auto_fix_incident_task(str(incident.id))
                print(f"Result: Auto-Fix Task Result: {result}")

            # 4. Veritabanında SystemImprovement kaydını kontrol et
            from sqlalchemy import select
            stmt = select(SystemImprovement).where(SystemImprovement.target_file == dummy_file)
            res = await session.execute(stmt)
            improvement = res.scalars().first()
            
            if improvement:
                print(f"OK: SystemImprovement generated: {improvement.id} | Status: {improvement.status}")
                print(f"OK: Instruction: {improvement.instruction}")
                
                # 5. Canary Check Simülasyonu
                print("Action: Simulating 15m Canary health check...")
                canary_res = verify_canary_health_task(str(incident.id))
                print(f"OK: Canary Check Result: {canary_res}")
            else:
                print("FAIL: No SystemImprovement was created.")

        finally:
            # Cleanup dummy file
            if os.path.exists(dummy_file):
                os.remove(dummy_file)
                print(f"Cleanup: Cleaned up dummy file: {dummy_file}")

    print("\n[PHASE 16 E2E] Test Completed.")

if __name__ == "__main__":
    asyncio.run(test_self_correction_flow())
