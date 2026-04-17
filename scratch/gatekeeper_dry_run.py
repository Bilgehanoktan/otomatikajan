import asyncio
import json
from libs.governance.launch_gatekeeper import LaunchGatekeeper

async def dry_run():
    print("--- LaunchGatekeeper DRY-RUN ---")
    print("Validating system readiness for Phase 30 Production-Scale Rollout...")
    
    passed, results = await LaunchGatekeeper.validate_for_rollout()
    
    print(f"\nOVERALL STATUS: {'[PASSED]' if passed else '[FAILED]'}")
    print("\nGATES ANALYSIS:")
    print(json.dumps(results, indent=2))
    
    if passed:
        print("\nPROCEED: System is eligible for single-project live pilot rollout.")
    else:
        print("\nBLOCK: System failed pre-flight checks. Resolve budget or governance gaps.")

if __name__ == "__main__":
    asyncio.run(dry_run())
