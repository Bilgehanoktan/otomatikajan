import asyncio
import pytest
from core.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_auto_initialization():
    # Create a fresh orchestrator instance (simulating a new process/worker)
    orch = Orchestrator()
    
    # Check that it starts as not running
    assert orch._is_running is False
    assert len(orch._agents) == 0
    
    # Call run_project (which should trigger auto-initialization)
    # We mock the planner to avoid full execution
    from unittest.mock import MagicMock
    orch.planner.plan = MagicMock(return_value=[])
    
    # We also need to mock start() side effects if we don't want to load real agents,
    # but here we want to test if build_agents() is called.
    # To keep it simple, we just check if _is_running becomes True.
    
    # We'll mock build_agents to return a dummy
    with pytest.MonkeyPatch().context() as m:
        m.setattr("core.orchestrator.build_agents", lambda: {"architect": MagicMock()})
        await orch.run_project("Test", "Test")
        
    assert orch._is_running is True
    assert "architect" in orch._agents
    assert "architect" in orch._health

if __name__ == "__main__":
    asyncio.run(test_orchestrator_auto_initialization())
