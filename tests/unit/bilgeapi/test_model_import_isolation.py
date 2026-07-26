import os
import subprocess
import sys
from pathlib import Path


def test_root_models_do_not_reimport_bilgeapi_database_under_an_alias():
    """Mixed root/BilgeAPI imports must not register the same tables twice."""
    repo_root = Path(__file__).resolve().parents[3]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root), str(repo_root / "apps"), env.get("PYTHONPATH", "")]
    )
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import bilgeapi.models.database; import libs.db.models; print('IMPORT_OK')",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert probe.returncode == 0, probe.stderr
    assert "IMPORT_OK" in probe.stdout


def test_root_repositories_import_with_root_only_pythonpath():
    """Worker images expose `/app` only and must not require `bilgeapi.*`."""
    repo_root = Path(__file__).resolve().parents[3]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import libs.db.repositories.repository; "
                "import libs.db.repositories.repair_repository; "
                "print('ROOT_REPOSITORIES_OK')"
            ),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert probe.returncode == 0, probe.stderr
    assert "ROOT_REPOSITORIES_OK" in probe.stdout
