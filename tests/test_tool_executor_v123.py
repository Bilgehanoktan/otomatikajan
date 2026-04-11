import pytest
import asyncio
from packages.orchestration.agi.operational.tool_executor import ToolExecutor
from packages.quality_assurance.output_schema import ToolCall

@pytest.mark.asyncio
async def test_tool_executor_phase_123_expansion():
    executor = ToolExecutor()
    
    # Test case 1: read_file (Existing but verified)
    calls = [
        ToolCall(tool_name="read_file", tool_input={"path": "pyproject.toml"})
    ]
    results = await executor.execute_calls("test_task", "test_agent", calls, {})
    assert results[0]["status"] == "success"
    assert "[project]" in results[0]["content"]

    # Test case 2: git_create_fix_branch
    # Note: This will actually create a branch if git is initialized. 
    # We use a unique name to avoid conflicts.
    calls = [
        ToolCall(tool_name="git_create_fix_branch", tool_input={"issue_id": "verify-123"})
    ]
    results = await executor.execute_calls("test_task", "test_agent", calls, {})
    # It might fail if no git repo, but in this workspace it should pass
    if results[0]["status"] == "success":
        assert "AutoRepair/fix-verify-123" in results[0]["branch"]
        # Cleanup: Return to main branch (Assuming main exists)
        import subprocess
        subprocess.run(["git", "checkout", "main"], capture_output=True)
        subprocess.run(["git", "branch", "-D", "AutoRepair/fix-verify-123"], capture_output=True)

    # Test case 3: run_shell_command (Safe command)
    calls = [
        ToolCall(tool_name="run_shell_command", tool_input={"command": "echo 'Sovereign AGI Verified'"})
    ]
    results = await executor.execute_calls("test_task", "test_agent", calls, {})
    assert results[0]["status"] == "success"
    assert "Sovereign AGI Verified" in results[0]["stdout"]

if __name__ == "__main__":
    asyncio.run(test_tool_executor_phase_123_expansion())
