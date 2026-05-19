import logging
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.ui_repair.security_posture_manager import SecurityPostureManager

logger = logging.getLogger(__name__)

class PostureRescanService:
    """Phase 22: Triggers a fresh security posture scan after remediation attempts."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.posture_manager = SecurityPostureManager(db)

    async def run_rescan(self, tenant_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs a new posture scan and returns the comparison results.
        """
        # 1. Run fresh scan
        new_posture = await self.posture_manager.run_posture_scan(tenant_key)
        
        # 2. Get previous score (simplified for now)
        # In a full implementation, we'd look up the last UISecurityPostureScore record
        
        return {
            "new_score": new_posture.overall_score,
            "posture_level": new_posture.posture_level.value,
            "scan_id": str(new_posture.id)
        }
