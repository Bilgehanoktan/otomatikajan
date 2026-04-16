import shutil
import subprocess
from pathlib import Path
from typing import Optional

from services.observability.logging import get_logger

logger = get_logger("git_ops")


class GitOps:
    """Self-update sonrası güvenli git işlemlerini yürütür."""

    def __init__(self, project_root: str | None = None):
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(__file__).resolve().parents[1]

    def _run_git(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )

    def is_git_available(self) -> bool:
        return shutil.which("git") is not None

    def is_git_repo(self) -> bool:
        if not self.is_git_available():
            return False

        result = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return result.returncode == 0 and result.stdout.strip() == "true"

    def commit_file(self, relative_path: str, message: str) -> Optional[str]:
        """
        Sadece ilgili dosya için commit dener.
        Git yoksa veya repo değilse None döner.
        """
        if not self.is_git_repo():
            logger.warning("Git repo bulunamadı veya git yüklü değil.")
            return None

        status = self._run_git(["status", "--porcelain", "--", relative_path])
        if status.returncode != 0:
            raise RuntimeError(status.stderr.strip() or "git status başarısız oldu")

        if not status.stdout.strip():
            logger.info(f"Commit gerektiren değişiklik yok: {relative_path}")
            return None

        add_result = self._run_git(["add", "--", relative_path])
        if add_result.returncode != 0:
            raise RuntimeError(add_result.stderr.strip() or "git add başarısız oldu")

        commit_result = self._run_git(["commit", "-m", message, "--", relative_path])
        combined_output = f"{commit_result.stdout}\n{commit_result.stderr}".strip()

        if commit_result.returncode != 0:
            if "nothing to commit" in combined_output.lower():
                logger.info("Git commit atlanıyor: nothing to commit")
                return None
            raise RuntimeError(combined_output or "git commit başarısız oldu")

        sha_result = self._run_git(["rev-parse", "--short", "HEAD"])
        if sha_result.returncode == 0:
            sha = sha_result.stdout.strip()
            logger.info(f"Git commit başarılı: {sha}")
            return sha

        return None
    def reset_to_sha(self, sha: str) -> bool:
        """Belirtilen SHA'ya hard reset atar."""
        if not self.is_git_repo():
            return False
            
        result = self._run_git(["reset", "--hard", sha])
        if result.returncode == 0:
            logger.info(f"Git reset başarılı: {sha}")
            return True
        else:
            logger.error(f"Git reset başarısız: {result.stderr.strip()}")
            return False

    def apply_patch(self, patch_content: str) -> bool:
        """
        Git patch dosyasını doğrudan sisteme uygular.
        """
        if not self.is_git_repo():
            return False
            
        patch_file = self.project_root / "temp_patch.patch"
        try:
            patch_file.write_text(patch_content, encoding="utf-8")
            result = self._run_git(["apply", str(patch_file)])
            
            if result.returncode == 0:
                logger.info("Patch başarıyla uygulandı.")
                return True
            else:
                logger.error(f"Patch uygulaması başarısız: {result.stderr.strip()}")
                return False
        finally:
            if patch_file.exists():
                patch_file.unlink()
