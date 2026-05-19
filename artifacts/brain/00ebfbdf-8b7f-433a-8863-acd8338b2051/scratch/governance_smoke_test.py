
import asyncio
import httpx
from datetime import datetime, timezone
import uuid

BASE_URL = "http://localhost:8000/api/v1"

async def smoke_test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("--- Governance Smoke Test ---")
        
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
            ("/repair/benchmarks", "Repair Benchmarks"),
        ]
        
        for path, name in endpoints:
            try:
                # Note: require_permission might block these if no token is provided.
                # In local dev, we might need a test token or bypass.
                # But let's see if they respond at all (even 401/403 is a response).
                resp = await client.get(f"{BASE_URL}{path}")
                status = resp.status_code
                print(f"[ {status} ] {name}: {path}")
                if status == 200:
                    data = resp.json()
                    count = len(data) if isinstance(data, list) else 1
                    print(f"      Count/Data: {count}")
            except Exception as e:
                print(f"[ ERROR ] {name}: {path} -> {e}")

if __name__ == "__main__":
    asyncio.run(smoke_test())
