
import httpx
import asyncio
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def test_resolve():
    # 1. Get an incident ID
    incident_id = "9f2a2858-3e19-4f48-8aa9-fd18dfc15200" # from user log
    
    # Generate token
    from services.auth.jwt_auth import _make_token
    from datetime import timedelta
    user_id = "2349b812-08a4-48f1-bfbd-da7c863b4f5c"
    token = _make_token({"sub": user_id, "type": "access", "role": "SOVEREIGN_PRIME"}, timedelta(minutes=15))

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"http://127.0.0.1:8000/api/v1/governance/incidents/{incident_id}/resolve",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "resolution_notes": "Test resolve via script",
                    "operator_id": user_id
                }
            )
            print(f"STATUS: {res.status_code}")
            print(f"BODY: {res.text}")
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_resolve())
