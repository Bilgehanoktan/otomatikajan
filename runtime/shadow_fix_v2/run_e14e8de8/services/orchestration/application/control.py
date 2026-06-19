import os
import json
from services.observability.logging import get_logger

_log = get_logger("system_control")

class SystemControl:
    """
    Sistem Kontrol Ünitesi (Application Layer).
    [Faz 12.1] Sistem duraklatma ve devam ettirme durumlarını merkezi olarak yönetir.
    """
    _instance = None
    _state_file = "workspace/system_state.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemControl, cls).__new__(cls)
            cls._instance._is_paused = False
            cls._instance.load_state()
        return cls._instance

    def load_state(self):
        try:
            if os.path.exists(self._state_file):
                with open(self._state_file, "r") as f:
                    data = json.load(f)
                    self._is_paused = data.get("is_paused", False)
                    _log.info(f"System state loaded: paused={self._is_paused}")
            else:
                self.save_state()
        except Exception as e:
            _log.error(f"Error loading system state: {e}")

    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            with open(self._state_file, "w") as f:
                json.dump({"is_paused": self._is_paused}, f)
        except Exception as e:
            _log.error(f"Error saving system state: {e}")

    def pause(self):
        self._is_paused = True
        self.save_state()
        _log.warning("SYSTEM PAUSED by user.")

    def resume(self):
        self._is_paused = False
        self.save_state()
        _log.info("SYSTEM RESUMED by user.")

    def is_paused(self) -> bool:
        return self._is_paused

system_control = SystemControl()
control = system_control # Alias for Faz 12.1 standards
