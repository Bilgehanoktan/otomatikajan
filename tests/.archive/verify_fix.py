import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from db.session import AsyncSessionLocal
from improve.observer import ImprovementObserver

async def verify_deterministic_ids():
    print("Running first scan...")
    async with AsyncSessionLocal() as db1:
        observer1 = ImprovementObserver(db1)
        scan1 = await observer1.scan()
        ids1 = [o.id for o in scan1]
    print(f"Scan 1 IDs: {ids1}")
    
    print("Running second scan...")
    async with AsyncSessionLocal() as db2:
        observer2 = ImprovementObserver(db2)
        scan2 = await observer2.scan()
        ids2 = [o.id for o in scan2]
    print(f"Scan 2 IDs: {ids2}")
    
    if not ids1:
        print("No opportunities found, verification incomplete (need data in metrics).")
        return
        
    if ids1 == ids2:
        print("SUCCESS: IDs are deterministic!")
    else:
        print("FAILURE: IDs changed between scans!")
        for i in range(min(len(ids1), len(ids2))):
            if ids1[i] != ids2[i]:
                print(f"Mismatch at index {i}: {ids1[i]} != {ids2[i]}")

if __name__ == "__main__":
    asyncio.run(verify_deterministic_ids())
