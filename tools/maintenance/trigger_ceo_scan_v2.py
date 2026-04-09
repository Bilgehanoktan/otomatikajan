import asyncio
import os
import sys

# PYTHONPATH set edilmeli
sys.path.append(os.getcwd())

print("DEBUG: Script started")

try:
    from packages.orchestration.ceo.engine import get_ceo_engine
    print("DEBUG: Imported get_ceo_engine")
except Exception as e:
    print(f"DEBUG: Import error: {e}")
    sys.exit(1)

async def main():
    print("DEBUG: Inside main")
    try:
        ceo = get_ceo_engine()
        print("DEBUG: Got CEO engine")
        await ceo.run_scan()
        print("DEBUG: CEO Scan tamamlandı.")
    except Exception as e:
        print(f"DEBUG: Execution error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
