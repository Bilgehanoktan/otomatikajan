"""
Soft CEO — Governor Config Management (Faz 6)
Loads and manages runtime thresholds from DB or defaults.
"""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.repositories.governor_calibration_repository import GovernorCalibrationRepo

# Default Thresholds
DEFAULTS = {
    "AUTO_APPROVE_MAX_RISK": 0.15,
    "AUTO_REPLAY_MAX_RISK": 0.35,
    "ARCHIVE_STALE_MIN_HOURS": 24,
    "PRIME_ESCALATION_MIN_RISK": 0.50,
    "FREEZE_MODE": 0.0 # 0.0 = False, 1.0 = True
}

# Safety Bounds
BOUNDS = {
    "AUTO_APPROVE_MAX_RISK": (0.05, 0.25),
    "AUTO_REPLAY_MAX_RISK": (0.15, 0.45),
    "ARCHIVE_STALE_MIN_HOURS": (12, 96),
    "PRIME_ESCALATION_MIN_RISK": (0.35, 0.70),
    "FREEZE_MODE": (0.0, 1.0)
}

class ApprovalGovernorConfig:

    @staticmethod
    async def get_threshold(db: AsyncSession, parameter_name: str) -> float:
        """En son uygulanan kalibrasyon değerini veya default'u döner."""
        active_val = await GovernorCalibrationRepo.get_active_value(db, parameter_name)
        if active_val is not None:
            return active_val
        return DEFAULTS.get(parameter_name, 0.0)

    @staticmethod
    async def get_auto_approve_max_risk(db: AsyncSession) -> float:
        return await ApprovalGovernorConfig.get_threshold(db, "AUTO_APPROVE_MAX_RISK")

    @staticmethod
    async def get_auto_replay_max_risk(db: AsyncSession) -> float:
        return await ApprovalGovernorConfig.get_threshold(db, "AUTO_REPLAY_MAX_RISK")

    @staticmethod
    async def get_archive_stale_min_hours(db: AsyncSession) -> int:
        val = await ApprovalGovernorConfig.get_threshold(db, "ARCHIVE_STALE_MIN_HOURS")
        return int(val)

    @staticmethod
    async def get_prime_escalation_min_risk(db: AsyncSession) -> float:
        return await ApprovalGovernorConfig.get_threshold(db, "PRIME_ESCALATION_MIN_RISK")

    @staticmethod
    async def is_frozen(db: AsyncSession) -> bool:
        val = await ApprovalGovernorConfig.get_threshold(db, "FREEZE_MODE")
        return val >= 0.5

    @staticmethod
    def get_defaults() -> Dict[str, float]:
        return DEFAULTS.copy()

    @staticmethod
    def get_bounds() -> Dict[str, Any]:
        return BOUNDS.copy()
