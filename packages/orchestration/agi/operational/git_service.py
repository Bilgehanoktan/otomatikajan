import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from packages.observability.logging import get_logger

_log = get_logger("agi_git_service")

class GitService:
    """
    Sovereign AGI Otonom Sürüm Kontrol Servisi (Phase 12.3).
    Sistemin kendi evrimini git branch ve commit mekanizmaları ile yönetmesini sağlar.
    """
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self._check_git_availability()

    def _check_git_availability(self):
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            _log.info("[GIT] Git servis erişilebilir.")
        except Exception:
            _log.error("[GIT] Git komutu bulunamadı veya erişilemez durumda.")

    def run_git(self, args: List[str]) -> Dict[str, Any]:
        """Git komutlarını güvenli bir şekilde çalıştırır."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "code": result.returncode
            }
        except Exception as e:
            _log.error(f"[GIT] Komut hatası ({args}): {e}")
            return {"success": False, "stdout": "", "stderr": str(e), "code": -1}

    def create_evolution_branch(self, feature_name: str) -> bool:
        """Yeni bir evrim dalı (branch) oluşturur."""
        branch_name = f"evolution/{feature_name.replace(' ', '_').lower()}_{int(os.path.getmtime('.'))}"
        _log.info(f"[GIT] Yeni evrim dalı oluşturuluyor: {branch_name}")
        
        # Branch var mı kontrol et, varsa switch
        res = self.run_git(["checkout", "-b", branch_name])
        return res["success"]

    def commit_evolution(self, message: str, files: Optional[List[str]] = None) -> bool:
        """Değişiklikleri evrim geçmişine kaydeder."""
        if files:
            for f in files:
                self.run_git(["add", f])
        else:
            self.run_git(["add", "."])
            
        res = self.run_git(["commit", "-m", f"[SOVEREIGN-EVOLUTION] {message}"])
        if res["success"]:
            _log.info(f"[GIT] Evrim kaydedildi: {message}")
        else:
            _log.warning(f"[GIT] Commit başarısız: {res['stderr']}")
        return res["success"]

    def rollback_last(self) -> bool:
        """Son yapılan değişikliği geri alır (Hard Reset)."""
        _log.warning("[GIT] Geri dönüş (Rollback) tetiklendi!")
        res = self.run_git(["reset", "--hard", "HEAD^"])
        return res["success"]

    def get_status(self) -> str:
        res = self.run_git(["status", "--short"])
        return res["stdout"]

# Singleton Instance
git_service = GitService()
