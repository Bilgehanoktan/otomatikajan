
import asyncio
import httpx
import jwt
from datetime import datetime, timezone, timedelta
import uuid

BASE_URL = "http://localhost:8000/api/v1"
JWT_SECRET = "8f9d0e1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e"
ADMIN_ID = "2349b812-08a4-48f1-bfbd-da7c863b4f5c"

def generate_token():
    payload = {
        "sub": ADMIN_ID,
        "email": "admin@sovereign.agi",
        "type": "access",
        "identity_type": "operator",
        "role": "SOVEREIGN_PRIME",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def smoke_test():
    token = generate_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("--- Governance AUTH'D Smoke Test ---")
        
        endpoints = [
            ("/governance/status", "Governance Status"),
            ("/governance/systemic-summary", "Systemic Summary"),
            ("/governance/fingerprints", "Fingerprints"),
            ("/governance/approvals", "Approvals"),
            ("/governance/improvements", "Improvements"),
            ("/governance/compliance/audit-bundles", "Audit Bundles"),
            ("/governance/incidents", "Incidents"),
            ("/governance/ops/launch-gates", "Launch Gates"),
            ("/governance/axiology", "Axiology (Proof)"),
            ("/governance/lineage", "Lineage (Proof)"),
            ("/governance/policies/evolution", "Policy Evolution"),
            ("/governance/drills", "Drills (Cases)"),
            ("/repair-lab/benchmarks", "Repair Lab Benchmarks"),
        ]
        
        for path, name in endpoints:
            try:
                resp = await client.get(f"{BASE_URL}{path}", headers=headers)
                status = resp.status_code
                print(f"[ {status} ] {name}: {path}")
                if status == 200:
                    data = resp.json()
                    count = len(data) if isinstance(data, list) else 1
                    print(f"      Count/Data: {count}")
                else:
                    print(f"      Error: {resp.text}")
            except Exception as e:
                print(f"[ ERROR ] {name}: {path} -> {e}")

if __name__ == "__main__":
    asyncio.run(smoke_test())
