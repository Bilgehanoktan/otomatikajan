"""
Verify BilgeAPI Alembic migration chain and write evidence.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _resolve_database_url(database_url: str | None) -> tuple[str | None, str]:
    if database_url:
        return database_url, "argument"

    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url, "environment"

    try:
        root = Path(__file__).resolve().parents[1]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from libs.config import DATABASE_URL

        return DATABASE_URL, "libs.config"
    except Exception:
        return None, "alembic.ini"


def _run(args: list[str], database_url: str | None) -> tuple[int, str]:
    env = os.environ.copy()
    if database_url:
        env["DATABASE_URL"] = database_url
    process = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        text=True,
        capture_output=True,
        env=env,
        timeout=60,
    )
    return process.returncode, (process.stdout + process.stderr).strip()


def verify(database_url: str | None) -> tuple[bool, list[str]]:
    effective_database_url, database_url_source = _resolve_database_url(database_url)
    heads_code, heads_output = _run(["heads"], effective_database_url)
    current_code, current_output = _run(["current"], effective_database_url)

    head_lines = [line.strip() for line in heads_output.splitlines() if "(head)" in line]
    current_matches_head = bool(head_lines) and any(line.split()[0] in current_output for line in head_lines)
    ok = heads_code == 0 and current_code == 0 and len(head_lines) == 1 and current_matches_head

    lines = [
        "# BilgeAPI Phase 18 Migration Verification",
        "",
        f"- Database URL source: `{database_url_source}`",
        f"- Single head: `{'yes' if len(head_lines) == 1 else 'no'}`",
        f"- Current matches head: `{'yes' if current_matches_head else 'no'}`",
        f"- Overall: `{'PASS' if ok else 'FAIL'}`",
        "",
        "## alembic heads",
        "```text",
        heads_output or "<empty>",
        "```",
        "",
        "## alembic current",
        "```text",
        current_output or "<empty>",
        "```",
    ]
    return ok, lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify BilgeAPI Alembic migration head/current alignment.")
    parser.add_argument("--database-url")
    parser.add_argument("--evidence", default="docs/evidence/bilgeapi_phase18_migration_verification.md")
    args = parser.parse_args()

    ok, lines = verify(args.database_url)
    output = "\n".join(lines) + "\n"
    print(output)
    evidence_path = Path(args.evidence)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(output, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
