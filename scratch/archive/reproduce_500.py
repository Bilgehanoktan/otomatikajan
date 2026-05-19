
import asyncio
import sys
from pathlib import Path
import uuid
from datetime import datetime, timezone

ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

async def reproduce_500():
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import OperationalIncident
    
    incident_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as db:
        # 1. Create a dummy incident
        inc = OperationalIncident(
            id=incident_id,
            incident_type="TEST_ERROR",
            severity="warning",
            message="Test incident for reproduction",
            status="open"
        )
        db.add(inc)
        await db.commit()
        print(f"Created incident: {incident_id}")

    # 2. Try to resolve it via API
    import httpx
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
                    "resolution_notes": "Attempting to reproduce 500",
                    "operator_id": user_id
                }
            )
            print(f"STATUS: {res.status_code}")
            print(f"BODY: {res.text}")
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce_500())
