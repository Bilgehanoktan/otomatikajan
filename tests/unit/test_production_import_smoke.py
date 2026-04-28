import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_IMPORT_MODULES = (
    "apps.public_api.main",
    "services.workflow_api.main",
)


def _production_env() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env.update(
        {
            "APP_ENV": "production",
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_company_test",
            "REDIS_URL": "redis://localhost:6379/0",
            "JWT_SECRET": "ci-test-secret-min64chars-padding-padding-padding-padding-padding",
            "ADMIN_SECRET": "ci-admin-secret",
            "ANTHROPIC_API_KEY": "ci-anthropic-key",
            "WEBHOOK_SECRET": "ci-webhook-secret-strong",
            "PYTHONPATH": (
                f"{REPO_ROOT}{os.pathsep}{pythonpath}" if pythonpath else str(REPO_ROOT)
            ),
        }
    )
    return env


@pytest.mark.smoke
@pytest.mark.parametrize("module_name", PRODUCTION_IMPORT_MODULES)
def test_production_module_import_smoke(tmp_path: Path, module_name: str) -> None:
    code = (
        "import importlib, sys; "
        f"sys.path.insert(0, {str(REPO_ROOT)!r}); "
        f"importlib.import_module({module_name!r}); "
        f"print({module_name!r} + ' production import ok')"
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=_production_env(),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, (
        f"{module_name} failed production import smoke test.\n"
        f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
    )
