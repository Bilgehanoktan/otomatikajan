import os
import json
from datetime import datetime, timezone
from services.observability.logging import get_logger

logger = get_logger("governance.standby")

class StandbyManager:
    STATE_FILE = "runtime/data/standby_control.json"
    TRIGGER_PHRASE = "Hazır, PRMR-01 Faz 1’i yeniden başlat."

    @staticmethod
    def _ensure_dir():
        os.makedirs(os.path.dirname(StandbyManager.STATE_FILE), exist_ok=True)

    @staticmethod
    def _read_state() -> dict:
        if not os.path.exists(StandbyManager.STATE_FILE):
            return {"reactivated": False, "last_transition": None, "trigger_count": 0}
        try:
            with open(StandbyManager.STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read standby state: {e}")
            return {"reactivated": False, "last_transition": None, "trigger_count": 0}

    @staticmethod
    def _write_state(state: dict):
        StandbyManager._ensure_dir()
        try:
            with open(StandbyManager.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to write standby state: {e}")

    @classmethod
    def is_in_standby(cls) -> bool:
        """Returns True if the system is currently in standby (not reactivated)."""
        state = cls._read_state()
        return not state.get("reactivated", False)

    @classmethod
    def check_trigger(cls, command: str) -> bool:
        """Checks if the command matches the trigger phrase and updates state if so."""
        if command.strip() == cls.TRIGGER_PHRASE:
            state = cls._read_state()
            state["reactivated"] = True
            state["last_transition"] = datetime.now(timezone.utc).isoformat()
            state["trigger_count"] = state.get("trigger_count", 0) + 1
            cls._write_state(state)
            logger.info("SYSTEM REACTIVATION TRIGGERED: Standby Mode EXITED.")
            return True
        
        logger.warning(f"Invalid reactivation attempted with command: {command}")
        return False

    @classmethod
    def reset_to_standby(cls):
        """Resets the system back to standby mode."""
        state = cls._read_state()
        state["reactivated"] = False
        state["last_transition"] = datetime.now(timezone.utc).isoformat()
        cls._write_state(state)
        logger.info("System reset to STANDBY MODE.")

    @classmethod
    def get_status_report(cls) -> dict:
        """Returns a human-readable status report for the gatekeeper."""
        state = cls._read_state()
        return {
            "mode": "STANDBY" if not state.get("reactivated") else "REACTIVATED",
            "trigger_phrase_enforced": True,
            "last_transition": state.get("last_transition"),
            "persistence_active": True
        }
