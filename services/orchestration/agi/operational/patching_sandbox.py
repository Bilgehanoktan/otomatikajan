"""
Patching Sandbox (Phase 36) — Safe Recursive Self-Modification.
AGI'nin kendi kaynak kodunu güvenli bir şekilde yamaması (Self-Patching) için birim.
Yedekleme, sentaks kontrolü ve atomik geri alma mekanizması sunar.
"""
import os
import shutil
import ast
import difflib
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from services.observability.logging import get_logger

_log = get_logger("agi_patching_sandbox")

class PatchingSandbox:
    """
    Operasyonel Güvenlik Katmanı (Katman 25+): Kendi Koduna Yazma Güvenliği.
    """
    def __init__(self, backup_dir: Optional[str] = None):
        # SOLIDIFIED ARCHITECTURE: Runtime data belongs to runtime/data
        if backup_dir is None:
            data_root = os.environ.get("DATA_DIR", "runtime/data")
            self.backup_dir = os.path.join(data_root, "backups", "self_patches")
        else:
            self.backup_dir = backup_dir
            
        os.makedirs(self.backup_dir, exist_ok=True)

    def apply_atomic_patch(self, file_path: str, new_content: str) -> Dict[str, Any]:
        """
        Dosyayı güvenli bir şekilde günceller.
        Süreç: Yedekle -> Sentaks Kontrolü -> Uygula -> Doğrula.
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        # 1. Yedekleme
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_name = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f"{file_name}.{ts}.bak")
        shutil.copy2(file_path, backup_path)
        _log.info(f"[SANDBOX] Backup created: {backup_path}")

        try:
            # 2. Sentaks Kontrolü (Python dosyaları için)
            if file_path.endswith(".py"):
                ast.parse(new_content)
                _log.debug(f"[SANDBOX] Syntax check PASSED for {file_path}")

            # 3. Yazma (Atomic Write - basitleştirilmiş)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            _log.info(f"[SANDBOX] Patch applied successfully: {file_path}")
            return {
                "success": True, 
                "backup": backup_path,
                "file": file_path,
                "timestamp": ts
            }

        except SyntaxError as se:
            _log.error(f"[SANDBOX] Syntax Error in proposed patch for {file_path}: {se}")
            # Do NOT apply patch, or rollback if needed (already backed up)
            self.rollback(file_path, backup_path)
            return {"success": False, "error": f"Syntax Error: {se}"}
        except Exception as e:
            _log.error(f"[SANDBOX] Unexpected error during patching {file_path}: {e}")
            self.rollback(file_path, backup_path)
            return {"success": False, "error": str(e)}

    def rollback(self, file_path: str, backup_path: str):
        """Yedek dosyadan geri yükleme yapar."""
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            _log.warning(f"[SANDBOX] ROLLBACK executed for {file_path} from {backup_path}")

    def generate_diff(self, old_content: str, new_content: str, file_name: str) -> str:
        """İnsan/Ajan okunabilirliği için diff üretir."""
        diff = difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            fromfile=f"old/{file_name}",
            tofile=f"new/{file_name}",
            lineterm=''
        )
        return '\n'.join(list(diff))

# Singleton
patching_sandbox = PatchingSandbox()
