from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
import os
from pathlib import Path

from services.repair.command_policy import validate_command
from services.repair.evidence_pack import REPO_ROOT
from services.repair.path_policy import is_forbidden_path
from services.repair.repair_models import RepairCandidate, RepairCase, SandboxResult
from services.repair.swe_rex_adapter import resolve_sandbox_backend


def _docker_available() -> bool:
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5, check=False)
        return result.returncode == 0
    except Exception:
        return False


def _ignore_for_sandbox(_: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in {
            ".git",
            ".venv",
            "node_modules",
            ".next",
            "__pycache__",
            ".pytest_cache",
            "repair_outputs",
            ".legacy_archive",
            ".backup",
            ".codex",
            ".nx",
            ".playwright-browsers",
            "brain",
            "scratch",
            "tmp",
            "tmp_test_outputs",
            "workspace",
        }
        or name.endswith(".pyc")
    }


def _copy_repo_to_temp(repo_root: Path) -> Path:
    temp_root = Path(tempfile.mkdtemp(prefix="egemen-yaz-repair-"))
    sandbox_root = temp_root / "repo"
    shutil.copytree(repo_root, sandbox_root, ignore=_ignore_for_sandbox)
    return sandbox_root


def _apply_patch(sandbox_root: Path, patch_path: Path, timeout_seconds: int) -> tuple[bool, str, str, int]:
    if not patch_path.exists() or patch_path.stat().st_size == 0:
        return True, "No patch content supplied; sandbox verification continued without applying changes.\n", "", 0

    result = subprocess.run(
        ["git", "apply", "--check", str(patch_path)],
        cwd=sandbox_root,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stdout, result.stderr, result.returncode

    apply_result = subprocess.run(
        ["git", "apply", str(patch_path)],
        cwd=sandbox_root,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return apply_result.returncode == 0, apply_result.stdout, apply_result.stderr, apply_result.returncode


def _run_docker_command(sandbox_root: Path, command_args: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    image = os.getenv("REPAIR_SANDBOX_IMAGE", "python:3.13-slim")
    docker_args = list(command_args)
    if docker_args and Path(docker_args[0]).name.lower() in {"py", "py.exe", "python.exe"}:
        docker_args[0] = "python"
    docker_command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "-v",
        f"{sandbox_root}:/workspace",
        "-w",
        "/workspace",
        image,
        *docker_args,
    ]
    return subprocess.run(
        docker_command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def run_patch_in_sandbox(
    candidate: RepairCandidate,
    repair_case: RepairCase,
    *,
    repo_root: Path | None = None,
    timeout_seconds: int = 60,
) -> SandboxResult:
    started = time.monotonic()
    root = repo_root or REPO_ROOT
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    failed_commands: list[str] = []

    forbidden_changes = [path for path in candidate.changed_files if is_forbidden_path(path, repair_case.forbidden_paths)]
    if forbidden_changes:
        return SandboxResult(
            patch_applied=False,
            tests_passed=False,
            failed_commands=["forbidden_path_guard"],
            stdout="",
            stderr=f"Patch candidate touches forbidden paths: {', '.join(forbidden_changes)}",
            duration_seconds=round(time.monotonic() - started, 4),
            exit_code=1,
        )

    patch_path = Path(candidate.patch_path)
    if (not patch_path.exists() or patch_path.stat().st_size == 0) and not repair_case.failed_command:
        return SandboxResult(
            patch_applied=True,
            tests_passed=True,
            failed_commands=[],
            stdout="No patch content and no failed_command supplied; sandbox applicability check passed without touching the source tree.\n",
            stderr="",
            duration_seconds=round(time.monotonic() - started, 4),
            exit_code=0,
        )

    backend = resolve_sandbox_backend()
    backend_name = str(backend.get("backend") or "local_temp")
    if backend.get("status") == "FALLBACK":
        stdout_parts.append(f"{backend.get('reason', 'Sandbox backend fallback applied')}\n")
    if backend_name == "swe_rex":
        stdout_parts.append("SWE-ReX backend secildi; dogrudan SWE-ReX execution bu fazda local_temp sandbox'a dusuruldu.\n")
        backend_name = "local_temp"

    use_docker = backend_name == "docker"
    if use_docker and not _docker_available():
        stdout_parts.append("Docker sandbox istendi fakat Docker bulunamadi; local_temp sandbox kullaniliyor.\n")
        use_docker = False
    if use_docker:
        stdout_parts.append("Docker detected; command verification will run in Docker after patch applicability checks.\n")

    sandbox_root: Path | None = None
    try:
        sandbox_root = _copy_repo_to_temp(root)
        patch_applied, apply_stdout, apply_stderr, apply_exit = _apply_patch(sandbox_root, patch_path, timeout_seconds)
        stdout_parts.append(apply_stdout)
        stderr_parts.append(apply_stderr)

        if not patch_applied:
            failed_commands.append("git apply --check")
            return SandboxResult(
                patch_applied=False,
                tests_passed=False,
                failed_commands=failed_commands,
                stdout="".join(stdout_parts),
                stderr="".join(stderr_parts),
                duration_seconds=round(time.monotonic() - started, 4),
                exit_code=apply_exit,
            )

        if not repair_case.failed_command:
            return SandboxResult(
                patch_applied=True,
                tests_passed=True,
                failed_commands=[],
                stdout="".join(stdout_parts) + "No failed_command supplied; patch applicability check passed.\n",
                stderr="".join(stderr_parts),
                duration_seconds=round(time.monotonic() - started, 4),
                exit_code=0,
            )

        command = repair_case.failed_command
        command_args = validate_command(command)
        if use_docker:
            docker_result = _run_docker_command(sandbox_root, command_args, timeout_seconds)
            if docker_result.returncode == 125:
                stdout_parts.append("Docker sandbox failed to start; falling back to local temp-copy command execution.\n")
                command_result = subprocess.run(
                    command_args,
                    cwd=sandbox_root,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            else:
                command_result = docker_result
        else:
            command_result = subprocess.run(
                command_args,
                cwd=sandbox_root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        stdout_parts.append(command_result.stdout)
        stderr_parts.append(command_result.stderr)
        if command_result.returncode != 0:
            failed_commands.append(command)

        return SandboxResult(
            patch_applied=True,
            tests_passed=command_result.returncode == 0,
            failed_commands=failed_commands,
            stdout="".join(stdout_parts),
            stderr="".join(stderr_parts),
            duration_seconds=round(time.monotonic() - started, 4),
            exit_code=command_result.returncode,
        )
    except subprocess.TimeoutExpired as exc:
        failed_commands.append(repair_case.failed_command or "sandbox_timeout")
        return SandboxResult(
            patch_applied=False,
            tests_passed=False,
            failed_commands=failed_commands,
            stdout="".join(stdout_parts) + (exc.stdout or ""),
            stderr="".join(stderr_parts) + f"Sandbox command timed out after {timeout_seconds}s.",
            duration_seconds=round(time.monotonic() - started, 4),
            exit_code=124,
        )
    except Exception as exc:
        return SandboxResult(
            patch_applied=False,
            tests_passed=False,
            failed_commands=failed_commands or ["sandbox_executor"],
            stdout="".join(stdout_parts),
            stderr="".join(stderr_parts) + str(exc),
            duration_seconds=round(time.monotonic() - started, 4),
            exit_code=1,
        )
    finally:
        if sandbox_root is not None:
            shutil.rmtree(sandbox_root.parent, ignore_errors=True)
