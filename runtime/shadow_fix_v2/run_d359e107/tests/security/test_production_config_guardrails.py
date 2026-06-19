import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_config_import(env_overrides: dict[str, str], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "production",
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_company_test",
            "ANTHROPIC_API_KEY": "ci-anthropic-key",
            "PYTHONPATH": str(REPO_ROOT),
        }
    )
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import libs.config; print('config import ok')"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_production_config_rejects_default_secrets(tmp_path: Path):
    completed = _run_config_import(
        {
            "JWT_SECRET": "sovereign-agi-control-plane-local-secret-stable-v1",
            "ADMIN_SECRET": "agi-admin-fallback-secret-2026",
            "WEBHOOK_SECRET": "your-webhook-secret",
        },
        tmp_path,
    )

    assert completed.returncode != 0
    assert "kabul edilemez" in completed.stderr


def test_production_config_accepts_strong_required_secrets(tmp_path: Path):
    completed = _run_config_import(
        {
            "JWT_SECRET": "ci-test-secret-min64chars-padding-padding-padding-padding-padding",
            "ADMIN_SECRET": "ci-admin-secret",
            "WEBHOOK_SECRET": "ci-webhook-secret-strong",
        },
        tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert "config import ok" in completed.stdout
