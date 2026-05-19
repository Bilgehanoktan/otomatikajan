import asyncio
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from services.governance.standby_manager import StandbyManager
from prmr_readiness_audit import run_audit

async def verify():
    print("--- Verifying Standby Persistence ---")
    
    # 1. Initial State
    print(f"Initial Status: {StandbyManager.get_status_report()['mode']}")
    
    # 2. Run Audit in Standby
    await run_audit()
    with open("docs/audits/infra_readiness_audit_prmr_01.md", "r", encoding="utf-8") as f:
        content = f.read()
        if "🔒 ACTIVE" in content:
            print("✓ Audit correctly shows ACTIVE Standby.")
        else:
            print("✗ Audit failed to show ACTIVE Standby.")

    # 3. Trigger Reactivation
    print("\nTriggering Reactivation...")
    trigger = "Hazır, PRMR-01 Faz 1’i yeniden başlat."
    success = StandbyManager.check_trigger(trigger)
    print(f"Reactivation Success: {success}")
    
    # 4. Final State
    print(f"Final Status: {StandbyManager.get_status_report()['mode']}")
    
    # 5. Run Audit in Reactivated
    await run_audit()
    with open("docs/audits/infra_readiness_audit_prmr_01.md", "r", encoding="utf-8") as f:
        content = f.read()
        if "🔓 REACTIVATED" in content:
            print("✓ Audit correctly shows REACTIVATED status.")
        else:
            print("✗ Audit failed to show REACTIVATED status.")

    # Clean up / Reset for real standby test
    # StandbyManager.reset_to_standby()

if __name__ == "__main__":
    asyncio.run(verify())
