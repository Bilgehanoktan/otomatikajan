from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILES = ("Dockerfile", "Dockerfile.bilgeapi", "Dockerfile.cms")


def test_dockerfiles_do_not_force_regional_debian_mirror() -> None:
    for name in DOCKERFILES:
        content = (REPO_ROOT / name).read_text(encoding="utf-8")

        assert "ftp.tr.debian.org" not in content, (
            f"{name} must retain Debian's default CDN instead of forcing a "
            "regional mirror"
        )


def test_cms_build_uses_scoped_frontend_context() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    cms_block = compose.split("\n  cms:\n", maxsplit=1)[1].split(
        "\n  db:\n", maxsplit=1
    )[0]
    dockerfile = (
        REPO_ROOT / "apps" / "refine_control_plane" / "Dockerfile.cms"
    ).read_text(encoding="utf-8")
    dockerignore = (
        REPO_ROOT / "apps" / "refine_control_plane" / ".dockerignore"
    ).read_text(encoding="utf-8")

    assert "context: ./apps/refine_control_plane" in cms_block
    assert "dockerfile: Dockerfile.cms" in cms_block
    assert "COPY package.json ./" in dockerfile
    assert "COPY package-lock.json ./" in dockerfile
    assert "npm ci --ignore-scripts --no-audit --no-fund" in dockerfile
    assert "COPY src ./src" in dockerfile
    assert "COPY public ./public" in dockerfile
    assert "COPY . ./" not in dockerfile
    assert dockerignore.splitlines()[0] == "*"
    assert (REPO_ROOT / "apps" / "refine_control_plane" / "package-lock.json").is_file()


def test_reconciled_store_runs_safe_startup_migrations_by_default() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    app_block = compose.split("\n  app:\n", maxsplit=1)[1].split(
        "\n  cms:\n", maxsplit=1
    )[0]
    bilgeapi_block = compose.split("\n  bilgeapi:\n", maxsplit=1)[1].split(
        "\nvolumes:\n", maxsplit=1
    )[0]

    assert 'RUN_DB_MIGRATIONS: ${RUN_DB_MIGRATIONS:-true}' in app_block
    assert 'RUN_DB_MIGRATIONS: ${RUN_DB_MIGRATIONS:-true}' in bilgeapi_block

    for name in ("Dockerfile", "Dockerfile.bilgeapi"):
        content = (REPO_ROOT / name).read_text(encoding="utf-8")
        assert '${RUN_DB_MIGRATIONS:-true}' in content
        assert "Skipping Alembic migrations" in content


def test_root_docker_context_excludes_root_node_modules() -> None:
    dockerignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "node_modules/" in dockerignore.splitlines()


def test_bilgeapi_runtime_contains_release_gate_dependencies() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")

    for package in ("defusedxml", "coverage", "ruff", "bandit"):
        assert any(
            line.split("=", 1)[0].split(">", 1)[0].strip() == package
            for line in requirements.splitlines()
        ), f"{package} must be installed in the BilgeAPI runtime image"


def test_bilgeapi_compose_uses_hash_only_static_keys() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    bilgeapi_block = compose.split("\n  bilgeapi:\n", maxsplit=1)[1].split(
        "\nvolumes:\n", maxsplit=1
    )[0]

    assert 'BILGEAPI_STATIC_KEYS: ""' in bilgeapi_block
    assert "BILGEAPI_STATIC_KEY_HASHES:" in bilgeapi_block
    assert "dev-test-key-001:ADMIN" not in bilgeapi_block


def test_bilgeapi_uses_monorepo_import_path_without_editable_install() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    dockerfile = (REPO_ROOT / "Dockerfile.bilgeapi").read_text(encoding="utf-8")
    bilgeapi_block = compose.split("\n  bilgeapi:\n", maxsplit=1)[1].split(
        "\nvolumes:\n", maxsplit=1
    )[0]

    assert "ENV PYTHONPATH=/app:/app/apps" in dockerfile
    assert "RUN pip install -e ." not in dockerfile
    assert "PYTHONPATH: /app:/app/apps" in bilgeapi_block
    assert "COPY apps/bilgeapi/requirements.txt /tmp/requirements.txt" in dockerfile
    assert "COPY apps/bilgeapi/requirements-dev.txt /tmp/requirements-dev.txt" in dockerfile
    assert "build-essential" not in dockerfile
