from fastapi import APIRouter, Depends
from apps.bilgeapi.auth import require_permission

router = APIRouter(prefix="/v1")

@router.get("/catalog", tags=["Catalog"])
async def get_catalog(_identity: dict = Depends(require_permission("bilgeapi.incident.read"))):
    return {
        "diagnostics": [
            {
                "name": "mock_agent",
                "description": "Deterministic diagnostic simulator"
            }
        ],
        "repair_dispatchers": [
            {
                "name": "webhook",
                "description": "Secure payload dispatch webhook adapter"
            }
        ]
    }

