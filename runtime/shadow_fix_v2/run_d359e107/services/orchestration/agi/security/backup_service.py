import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone
from services.observability.logging import get_logger

_log = get_logger("agi_backup_service")

class BackupService:
    """
    Sovereign AGI Shadow Backup Service (Phase 35).
    Otonom kod müdahalelerinden önce dosyaların mevcut halini korur.
    """
    BACKUP_DIR = Path(".backup")

    def __init__(self):
        if not self.BACKUP_DIR.exists():
            self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: str) -> str:
        """
        Dosyayı zaman damgali olarak yedekler.
        Dönen değer: backup_id (dosya yolu)
        """
        if not os.path.exists(file_path):
            _log.warning(f"Dosya bulunamadı, yedeklenemedi: {file_path}")
            return ""

        try:
            # Örn: e:/project/core/api.py -> .backup/core/api.py_20260401T065000Z.bak
            now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            rel_path = os.path.relpath(file_path, ".")
            backup_name = f"{rel_path}_{now}.bak"
            target_path = self.BACKUP_DIR / backup_name
            
            # Alt dizinleri oluştur
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(file_path, target_path)
            _log.info(f"[BACKUP] Gölge yedek oluşturuldu: {target_path}")
            return str(target_path)
        except Exception as e:
            _log.error(f"[BACKUP] Yedekleme hatası ({file_path}): {e}")
            return ""

    def restore_backup(self, original_path: str, backup_path: str) -> bool:
        """Belirtilen yedeği orijinal konumuna geri yükler."""
        if not os.path.exists(backup_path):
            _log.error(f"Geri yükleme hatası: Yedek dosyası bulunamadı ({backup_path})")
            return False

        try:
            shutil.copy2(backup_path, original_path)
            _log.warning(f"[ROLLBACK] Dosya geri yüklendi: {original_path} (Kaynak: {backup_path})")
            return True
        except Exception as e:
            _log.error(f"[ROLLBACK] Geri yükleme hatası: {e}")
            return False

    def cleanup(self, max_age_days: int = 7):
        """Eski yedekleri temizler."""
        now = time.time()
        for root, dirs, files in os.walk(self.BACKUP_DIR):
            for f in files:
                f_path = os.path.join(root, f)
                if os.stat(f_path).st_mtime < now - (max_age_days * 86400):
                    os.remove(f_path)
                    _log.debug(f"Eski yedek temizlendi: {f}")

# Singleton Instance
backup_service = BackupService()
