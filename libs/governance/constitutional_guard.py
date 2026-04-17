"""
governance/constitutional_guard.py — Phase 30
Sistem çekirdeğini otonom değişikliklere karşı koruyan güvenlik katmanı.
"""

import os
from pathlib import Path
from typing import List, Set

# Otonom gelişim döngüsünün ASLA doğrudan değiştiremeyeceği kritik yollar.
# Bu dosyalar için sadece "Öneri" (Advisory) modunda çalışılabilir.
CONSTITUTIONAL_LOCK_LIST: Set[str] = {
    "libs/db/base.py",
    "libs/db/session.py",
    "libs/auth/",                       # Tüm klasör
    "services/auth/",                   # Tüm klasör
    "libs/governance/",                 # Kendini korumalı
    "libs/llm/cost_tracker.py",         # Bütçe denetçisi
    "libs/llm/cost_calc.py",
    "services/governance/lineage_service.py",
    "emergency_policy.py",
    "constitution.md",
}

import yaml # Phase 30

class ConstitutionalGuard:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.config_path = self.project_root / "config" / "governance" / "constitutional_locks.yaml"
        self._lock_list: Set[str] = self._load_locks()

    def _load_locks(self) -> Set[str]:
        """Yapılandırma dosyasından kilit listesini yükler."""
        locks = set(CONSTITUTIONAL_LOCK_LIST) # Fallback to hardcoded
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    if config and "locked_paths" in config:
                        locks.update(config["locked_paths"])
                    if config and "overlays" in config:
                        locks.update(config["overlays"])
            except Exception as e:
                # Log rotation error here if needed
                pass
        return locks

    def is_locked(self, file_path: str) -> bool:
        """
        Belirtilen dosya yolunun anayasal olarak kilitli olup olmadığını kontrol eder.
        """
        try:
            full_path = Path(file_path).resolve()
            # Proje köküne göre normalize et
            try:
                rel_path = str(full_path.relative_to(self.project_root)).replace("\\", "/")
            except ValueError:
                # Proje dışı bir dosya ise güvenlik gereği kilitli say
                return True

            for locked_path in self._lock_list:
                # Klasör kontrolü (klasör ismiyle başlıyorsa veya '/' ile bitiyorsa)
                if locked_path.endswith("/") and rel_path.startswith(locked_path):
                    return True
                # Dosya kontrolü (tam eşleşme)
                if rel_path == locked_path:
                    return True
            
            return False
        except Exception:
            # Herhangi bir hata durumunda "fail-safe" olarak kilitli kabul et
            return True

    def get_protected_paths(self) -> List[str]:
        return list(self._lock_list)

