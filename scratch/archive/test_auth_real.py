
import asyncio
import sys
from pathlib import Path
from datetime import timedelta
import httpx

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def test_auth_me():
    from services.auth.jwt_auth import _make_token
    
    # 1. Generate Token
    user_id = "2349b812-08a4-48f1-bfbd-da7c863b4f5c"
    email = "admin@sovereign.agi"
    role = "SOVEREIGN_PRIME"
    
    token = _make_token({
        "sub": user_id,
        "email": email,
        "type": "access",
        "identity_type": "operator",
        "role": role
    }, timedelta(minutes=15))
    
    print(f"TOKEN: {token[:20]}...")
    
    # 2. Call API
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                "http://127.0.0.1:8000/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"STATUS: {res.status_code}")
            print(f"BODY: {res.text}")
        except Exception as e:
            print(f"REQUEST FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_me())
