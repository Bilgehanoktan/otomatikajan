
import asyncio
import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_live_flow():
    async with httpx.AsyncClient() as client:
        print("--- Scanning for improvements ---")
        try:
            r = await client.get(f"{BASE_URL}/improvements/scan")
            if r.status_code != 200:
                print(f"FAILED: Scan returned {r.status_code}")
                return
            
            improvements = r.json()
            print(f"Found {len(improvements)} improvements.")
            
            if not improvements:
                print("No improvements to test application with.")
                return
            
            target = improvements[0]
            # Handle both new and old format
            target_id = target.get("id") or f"prop_{improvements.index(target)}"
            
            print(f"Applying improvement: {target_id}")
            r_apply = await client.post(f"{BASE_URL}/improvements/apply-proposal/{target_id}")
            
            if r_apply.status_code == 200:
                print(f"SUCCESS: {r_apply.json().get('message')}")
            else:
                print(f"FAILED: Apply returned {r_apply.status_code} - {r_apply.text}")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    # Note: This requires the server to be running.
    # If the server is not running, we'll see a connection error.
    asyncio.run(test_live_flow())
