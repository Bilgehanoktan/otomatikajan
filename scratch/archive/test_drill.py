import asyncio
import os
import sys

# Project root ekle
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from services.repair.repair_orchestrator import RepairOrchestrator
from services.repair.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
from libs.db.session import init_db

async def test_drill():
    print("--- Governance Drill Test (Resilience Mode) ---")
    
    # 1. DB Başlat (SQLite Fallback tetiklensin)
    print("DB Initializing...")
    await init_db()
    
    orchestrator = RepairOrchestrator()
    
    # Mock incident
    incident = IncidentRecord(
        incident_id="drill-test-01",
        source=IncidentSource.GOVERNANCE,
        severity=IncidentSeverity.HIGH,
        service="governance",
        module="libs/db/session.py",
        symptom="ConnectionRefusedError: DB Connection failed during drill",
        stack_trace="Traceback...",
        context={"scenario": "RESILIENCE_DRILL_01"}
    )
    
    print(f"Starting shadow repair cycle for scenario: {incident.context['scenario']}...")
    try:
        # Shadow cycle veritabanına dokunur (Learning/Evidence)
        result = await orchestrator.shadow_repair_cycle("RESILIENCE_DRILL_01", incident.to_dict())
        print(f"Result: {result['status']}")
        print(f"Winner: {result['winner_strategy']} (Score: {result['winning_score']})")
        
        # Stats kontrolü
        stats = orchestrator.stats()
        print(f"Orchestrator Stats - Total Jobs: {stats['total']}")
        
        print("\nDrill completed successfully!")
    except Exception as e:
        print(f"\nDrill FAILED with unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_drill())
