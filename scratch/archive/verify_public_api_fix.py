
import asyncio
import os
import sys
from pathlib import Path

# Project root path
ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def test_public_api_repair_summary():
    print("Testing Public API - Repair Health Summary...")
    try:
        from apps.public_api.main import _get_repair_health_summary
        summary = _get_repair_health_summary()
        print(f"Repair Health Summary: {summary}")
        
        if summary.get("available") is False:
            print("FAILED: Repair Orchestrator is still not available.")
            sys.exit(1)
        else:
            print("SUCCESS: Repair Orchestrator is reachable and returning stats.")
            
    except Exception as e:
        print(f"ERROR: Testing failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_public_api_repair_summary())
