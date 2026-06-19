import json
import os
from typing import List, Set

class SafetyGate:
    """
    GStack /freeze ve /guard mantigini uygulayan guvenlik katmani.
    Kritik dosyalarin otonom ajanlar tarafindan degistirilmesini engeller.
    """
    def __init__(self, config_path: str = "config/safety_gate.json"):
        self.config_path = config_path
        self.frozen_files: Set[str] = set()
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.frozen_files = set(data.get("frozen_files", []))
            except Exception:
                pass

    def save_config(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump({"frozen_files": list(self.frozen_files)}, f, indent=2)

    def freeze(self, file_path: str):
        """Dosyayi koruma altina alir."""
        self.frozen_files.add(file_path)
        self.save_config()

    def unfreeze(self, file_path: str):
        """Dosya korumasini kaldirir."""
        if file_path in self.frozen_files:
            self.frozen_files.remove(file_path)
            self.save_config()

    def is_frozen(self, file_path: str) -> bool:
        """Dosya su an dondurulmus mu?"""
        # Tam yol veya dosya adi bazli kontrol
        return any(frozen in file_path for frozen in self.frozen_files)

    def check_access(self, file_path: str):
        """Eger dosya dondurulmussa hata firlatir."""
        if self.is_frozen(file_path):
            raise PermissionError(f"GUVENLIK IHLALI: '{file_path}' dosyasi dondurulmus (frozen) durumda ve degistirilemez.")

safety_gate = SafetyGate()
