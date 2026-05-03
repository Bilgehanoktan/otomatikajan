import ast
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

from services.observability.logging import get_logger

logger = get_logger("shadow_runner")


class ShadowRunner:
    """
    Canlıya yazmadan önce proje kopyasını shadow workspace altında oluşturur,
    yeni dosyayı oraya enjekte eder, syntax ve mümkünse pytest doğrulaması yapar.
    """

    GLOBAL_EXCLUDES = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".pytest_cache",
        "vendor",
        "shadow_workspace", # CRITICAL: Fix recursive copying
        "runtime",          # Phase 12.1: Exclude runtime directory
        "artifacts",
        "brain",
        ".legacy_archive",
        ".backup",
        "docs",
        "performance",
        "e2e",
        "tmp",              # WinError 5 Fix
        "temp",
        ".pytest_cache",
        ".idea",
        ".vscode"
    }

    def __init__(self, project_root: str | None = None, timeout_seconds: int = 180):
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(__file__).resolve().parents[3]

        self.timeout_seconds = timeout_seconds

    def _copy_ignore(self, directory: str, names: list[str]) -> set[str]:
        current = Path(directory)
        ignored = set()

        for name in names:
            if name in self.GLOBAL_EXCLUDES:
                ignored.add(name)

        if current.name == "workspace":
            for name in {"backups", "shadow_workspace"}:
                if name in names:
                    ignored.add(name)

        return ignored

    def _has_test_suite(self, root: Path) -> bool:
        if (root / "tests").exists():
            return True
        if (root / "pytest.ini").exists():
            return True
        if (root / "tox.ini").exists():
            return True
        if (root / "pyproject.toml").exists():
            return True
        return False

    def _validate_syntax(self, file_path: Path, code: str) -> None:
        if file_path.suffix == ".py":
            ast.parse(code, filename=str(file_path))
            compile(code, str(file_path), "exec")
        elif file_path.suffix in (".tsx", ".ts"):
            # Node.js ortamı olmadığı durumlarda LLM regex validasyonuna güvenilir (SelfUpdater tarafında)
            # Eğer ortamda tsc kuruluysa ve node_modules varsa burada tsc çalıştırılabilir.
            if not code.strip():
                raise ValueError("TSX dosyası boş olamaz.")
        elif file_path.suffix == ".css":
            if not code.strip():
                raise ValueError("CSS dosyası boş olamaz.")

    def validate_candidate(self, relative_path: str, candidate_code: str) -> Dict[str, Any]:
        run_id = uuid.uuid4().hex[:8]
        shadow_root = self.project_root / "runtime" / "shadow_fix_v2" / f"run_{run_id}"

        logger.info(f"Shadow ortam hazırlanıyor: {shadow_root}")
        shutil.copytree(
            self.project_root,
            shadow_root,
            ignore=self._copy_ignore,
        )

        shadow_target = shadow_root / relative_path
        shadow_target.parent.mkdir(parents=True, exist_ok=True)
        shadow_target.write_text(candidate_code, encoding="utf-8")

        result: Dict[str, Any] = {
            "shadow_root": str(shadow_root),
            "shadow_target": str(shadow_target),
            "syntax_ok": False,
            "pytest_ok": None,
            "pytest_skipped": False,
            "stdout": "",
            "stderr": "",
            "returncode": None,
        }

        try:
            self._validate_syntax(shadow_target, candidate_code)
            result["syntax_ok"] = True
            logger.info(f"Syntax doğrulama başarılı: {shadow_target}")
        except Exception as e:
            result["stderr"] = f"Syntax validation failed: {e}"
            logger.error(result["stderr"])
            return result

        pytest_binary = shutil.which("pytest")
        if not pytest_binary or not self._has_test_suite(shadow_root):
            result["pytest_skipped"] = True
            logger.warning("Pytest atlandı: pytest yok veya test suite bulunamadı.")
            return result

        try:
            proc = subprocess.run(
                [pytest_binary, "-q"],
                cwd=str(shadow_root),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["returncode"] = proc.returncode
            result["pytest_ok"] = proc.returncode == 0

            if proc.returncode == 0:
                logger.info("Shadow pytest başarılı.")
            else:
                logger.error("Shadow pytest başarısız.")
        except subprocess.TimeoutExpired as e:
            result["stderr"] = f"Pytest timeout: {e}"
            result["pytest_ok"] = False
            logger.error(result["stderr"])
        except Exception as e:
            result["stderr"] = f"Pytest execution failed: {e}"
            result["pytest_ok"] = False
            logger.error(result["stderr"])

        return result
