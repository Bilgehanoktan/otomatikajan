from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .maintenance_policy import MaintenancePolicy

class MaintenanceWindowManager:
    @staticmethod
    async def is_in_maintenance_window(db: AsyncSession, project_key: str) -> bool:
        policy = await MaintenancePolicy.get_policy(db, project_key)
        if not policy:
            return True # Default to True if no policy? Or False? Usually GA requires policy.
            
        window = policy.maintenance_window_json
        if not window:
            return True
            
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.weekday() # 0 is Monday
        
        start = window.get("start_time", "00:00")
        end = window.get("end_time", "23:59")
        allowed_days = window.get("days", [0,1,2,3,4,5,6])
        
        if current_day not in allowed_days:
            return False
            
        if start <= current_time <= end:
            return True
            
        return False

    @staticmethod
    async def check_action_allowed(db: AsyncSession, project_key: str, action: str) -> bool:
        policy = await MaintenancePolicy.get_policy(db, project_key)
        if not policy:
            return True
            
        if action in policy.blocked_actions_json:
            return False
            
        if action in policy.allowed_actions_json:
            return True
            
        # Default behavior: High-risk actions might be blocked outside window
        if action == "AUTO_APPLY" and not await MaintenanceWindowManager.is_in_maintenance_window(db, project_key):
            return False
            
        return True
