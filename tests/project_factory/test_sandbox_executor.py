from __future__ import annotations

import pytest
from pathlib import Path
from services.project_factory.sandbox_executor import check_command_safety, execute_sandbox_command

def test_command_safety_whitelist():
    # Approved commands should not raise ValueError
    check_command_safety("npm run build")
    check_command_safety("npm run lint")
    check_command_safety("npm test")
    check_command_safety("py -3.13 -m pytest")
    check_command_safety("py -3.13 -m compileall")

def test_command_safety_blacklist():
    # Command chaining or redirection must throw ValueError
    unsafe_commands = [
        "npm run build && echo 'pwned'",
        "npm run build & echo 'pwned'",
        "npm run lint || echo 'pwned'",
        "npm test ; rm -rf /",
        "py -3.13 -m pytest > output.txt",
        "py -3.13 -m pytest >> output.txt",
        "py -3.13 -m pytest < input.txt",
        "py -3.13 -m pytest | grep Error",
        "npm run build $(whoami)",
        "npm run build `whoami`",
        "git push origin master",
        "git commit -m 'evil'",
        "docker run -it alpine",
        "curl http://malicious.site",
        "wget http://malicious.site",
        "env dump",
        "powershell Start-Process notepad.exe"
    ]
    for cmd in unsafe_commands:
        with pytest.raises(ValueError):
            check_command_safety(cmd)

def test_execute_sandbox_command_non_existent_dir():
    # Non-existent sandbox directory should throw FileNotFoundError
    with pytest.raises(FileNotFoundError):
        execute_sandbox_command("PF-123", "npm run build", Path("non_existent_dir_12345"))
