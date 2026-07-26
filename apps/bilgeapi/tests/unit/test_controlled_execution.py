import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from bilgeapi.config import settings
from bilgeapi.governance.policy_engine import PolicyEngine
from bilgeapi.governance.risk_engine import RiskEngine
from bilgeapi.execution.rollback_manager import RollbackManager
from bilgeapi.execution.quarantine import QuarantineManager
from bilgeapi.execution.file_executor import FileExecutor
from bilgeapi.execution.command_executor import SafeCommandExecutor
from bilgeapi.execution.controlled_execution import ControlledExecutionEngine

# Mock permissions configurations
mock_permissions = {
    "permissions": {
        "allow": ["git diff", "pytest", "npm test", "Write", "Edit", "Rename"],
        "deny": ["rm *", "sudo *", "wget *", "curl *"],
        "ask": []
    }
}

mock_delete_policy = {
    "policy": {
        "forbidden": ["**/.git/**/*", "**/audit.log"],
        "approval_required": ["**/.env*"],
        "quarantine": [],
        "auto_delete": []
    }
}

mock_task_policy = {
    "policy": {
        "retry_limit": 3,
        "low_risk_auto_execute": True
    }
}


@pytest.fixture
def execution_env():
    """Sets up a temporary sandbox environment with mocked policy components."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()
        workspace_path = tmp_path / ".bilgeapi"
        workspace_path.mkdir()
        
        # Risk and Policy Engine setups
        risk_engine = RiskEngine(risk_rules=[])
        policy_engine = PolicyEngine(
            permissions_cfg=mock_permissions,
            delete_policy_cfg=mock_delete_policy,
            task_policy_cfg=mock_task_policy,
            risk_engine=risk_engine
        )
        
        # Managers
        rollback_manager = RollbackManager(project_root=tmp_path, workspace_dir=workspace_path)
        quarantine_manager = QuarantineManager(project_root=tmp_path, workspace_dir=workspace_path)
        
        # File Executor
        file_executor = FileExecutor(
            project_root=tmp_path,
            workspace_dir=workspace_path,
            policy_engine=policy_engine,
            rollback_manager=rollback_manager,
            quarantine_manager=quarantine_manager
        )
        
        # Command Executor
        command_executor = SafeCommandExecutor(
            project_root=tmp_path,
            workspace_dir=workspace_path,
            policy_engine=policy_engine
        )
        
        # Controlled Execution Engine
        engine = ControlledExecutionEngine(
            file_executor=file_executor,
            command_executor=command_executor,
            rollback_manager=rollback_manager
        )
        
        yield {
            "root": tmp_path,
            "workspace": workspace_path,
            "policy_engine": policy_engine,
            "rollback_manager": rollback_manager,
            "file_executor": file_executor,
            "command_executor": command_executor,
            "engine": engine
        }


# ─────────────────────────────────────────────────────────────────────────────
# 1. SafeCommandExecutor Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_command_executor_allowed_commands(execution_env):
    cmd_exec = execution_env["command_executor"]
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="diff output", stderr="")
        res = cmd_exec.execute_command("git diff")
        assert res["status"] == "SUCCESS"
        assert res["exit_code"] == 0
        assert res["stdout"] == "diff output"


def test_command_executor_denied_by_allowlist(execution_env):
    cmd_exec = execution_env["command_executor"]
    
    # "cat /etc/passwd" is not allowed in permissions
    with pytest.raises(PermissionError) as exc:
        cmd_exec.execute_command("cat /etc/passwd")
    assert "requires human approval" in str(exc.value)


def test_command_executor_hardcoded_denylist(execution_env):
    cmd_exec = execution_env["command_executor"]
    
    # Denylist keywords must fail with ValueError
    with pytest.raises(ValueError) as exc:
        cmd_exec.execute_command("rm -rf /")
    assert "forbidden keyword: rm" in str(exc.value)

    with pytest.raises(ValueError) as exc2:
        cmd_exec.execute_command("wget http://malicious.site")
    assert "forbidden token/character" in str(exc2.value)


# ─────────────────────────────────────────────────────────────────────────────
# 2. FileExecutor Dry-Run Mode Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_file_executor_dry_run_write(execution_env):
    file_exec = execution_env["file_executor"]
    root = execution_env["root"]
    
    # 1. Write initially in dry-run
    file_exec.set_dry_run(True)
    res = file_exec.write_file("main.py", "print('hello')")
    
    assert res["status"] == "SUCCESS"
    assert res["action"] == "WRITE_DRY_RUN"
    assert "diff" in res
    assert "hello" in res["diff"]
    
    # Verify file does NOT exist on disk yet
    target_file = root / "main.py"
    assert not target_file.exists()
    assert "main.py" in file_exec.dry_run_files

    # 2. Apply the dry run changes
    apply_res = file_exec.apply_dry_run_changes(approved=True)
    assert len(apply_res) == 1
    assert apply_res[0]["action"] == "WRITE"
    
    # Verify file exists on disk now
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "print('hello')"
    assert len(file_exec.dry_run_files) == 0


def test_file_executor_dry_run_patch(execution_env):
    file_exec = execution_env["file_executor"]
    root = execution_env["root"]
    
    target_file = root / "main.py"
    target_file.write_text("def run():\n    pass\n", encoding="utf-8")
    
    file_exec.set_dry_run(True)
    res = file_exec.patch_file("main.py", "pass", "print('patched')")
    
    assert res["status"] == "SUCCESS"
    assert res["action"] == "PATCH_DRY_RUN"
    assert "+    print('patched')" in res["diff"]
    
    # File content on disk should still be unchanged
    assert "pass" in target_file.read_text(encoding="utf-8")
    assert "main.py" in file_exec.dry_run_files


# ─────────────────────────────────────────────────────────────────────────────
# 3. ControlledExecutionEngine Transaction & Rollback Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_controlled_execution_success(execution_env):
    engine = execution_env["engine"]
    root = execution_env["root"]
    
    target_file = root / "utils.py"
    target_file.write_text("old content", encoding="utf-8")
    
    files_to_modify = [
        {"action": "write", "filepath": "main.py", "content": "print('ok')"},
        {"action": "patch", "filepath": "utils.py", "original_snippet": "old content", "replacement_snippet": "new content"}
    ]
    
    with patch("subprocess.run") as mock_run:
        # Simulate successful pytest
        mock_run.return_value = MagicMock(returncode=0, stdout="all tests passed", stderr="")
        
        tx_res = engine.execute_transaction(
            files_to_modify=files_to_modify,
            test_command="pytest",
            approved=True
        )
        
        assert tx_res["status"] == "COMMIT"
        assert (root / "main.py").read_text(encoding="utf-8") == "print('ok')"
        assert (root / "utils.py").read_text(encoding="utf-8") == "new content"


def test_controlled_execution_failure_rolls_back(execution_env):
    engine = execution_env["engine"]
    root = execution_env["root"]
    
    # Initialize files
    utils_file = root / "utils.py"
    utils_file.write_text("original utils", encoding="utf-8")
    
    files_to_modify = [
        {"action": "write", "filepath": "main.py", "content": "corrupted main"},
        {"action": "patch", "filepath": "utils.py", "original_snippet": "original utils", "replacement_snippet": "corrupted utils"}
    ]
    
    with patch("subprocess.run") as mock_run:
        # Simulate failed test run (exit code 1)
        mock_run.return_value = MagicMock(returncode=1, stdout="pytest failed", stderr="")
        
        tx_res = engine.execute_transaction(
            files_to_modify=files_to_modify,
            test_command="pytest",
            approved=True
        )
        
        assert tx_res["status"] == "ROLLBACK"
        
        # main.py should have been deleted because it did not exist before tx
        assert not (root / "main.py").exists()
        
        # utils.py should have been restored to its original state
        assert utils_file.read_text(encoding="utf-8") == "original utils"
