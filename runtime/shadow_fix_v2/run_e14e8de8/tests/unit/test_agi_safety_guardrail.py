import pytest
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from services.orchestration.agi.cognitive.agi_goal_decomposer import GoalDecomposer, agi_goal_decomposer

@pytest.mark.asyncio
async def test_safety_guardrail_allows_legitimate_scan():
    """Verify that a safe target scan like 'sistemdiltaraması yap' is not blocked by safety filters."""
    decomposer = GoalDecomposer()
    decomposer.model_orch = AsyncMock()
    
    # Mock complete_task to return a valid structured plan JSON
    mock_plan = {
        "plan": [
            {
                "step_id": "step_0",
                "agent_id": "translator",
                "prompt": "Scan translation files.",
                "is_complex": False,
                "dependencies": []
            }
        ]
    }
    decomposer.model_orch.complete_task.return_value = MagicMock(content=json.dumps(mock_plan))
    
    # Run decomposer
    subtasks = await decomposer.decompose(
        title="sistemdiltaraması yap",
        description="Verify system languages and translations",
        available_agents=[{"id": "translator", "name": "Translator", "role": "translator"}]
    )
    
    # Verify it passed the safety block and completed the task via model orchestrator
    assert len(subtasks) == 1
    assert subtasks[0].agent_id == "translator"
    decomposer.model_orch.complete_task.assert_called_once()

@pytest.mark.asyncio
async def test_safety_guardrail_allows_substring_banned_words():
    """Verify that words like 'temsilci' (containing 'sil' as substring) are not blocked."""
    decomposer = GoalDecomposer()
    decomposer.model_orch = AsyncMock()
    
    mock_plan = {
        "plan": [
            {
                "step_id": "step_0",
                "agent_id": "architect",
                "prompt": "Check representatives",
                "is_complex": False,
                "dependencies": []
            }
        ]
    }
    decomposer.model_orch.complete_task.return_value = MagicMock(content=json.dumps(mock_plan))
    
    subtasks = await decomposer.decompose(
        title="sistem temsilcilerini kontrol et",
        description="Verify user representatives in system",
        available_agents=[{"id": "architect", "name": "Architect", "role": "architect"}]
    )
    
    assert len(subtasks) == 1
    decomposer.model_orch.complete_task.assert_called_once()

@pytest.mark.asyncio
async def test_safety_guardrail_blocks_actual_malicious_commands():
    """Verify that actual malicious instructions on sensitive system components are blocked."""
    decomposer = GoalDecomposer()
    decomposer.model_orch = AsyncMock()
    
    # Run decomposer on a dangerous command
    subtasks = await decomposer.decompose(
        title="sistem verilerini sil",
        description="Delete all target system database schemas and user data",
        available_agents=[{"id": "architect", "name": "Architect", "role": "architect"}]
    )
    
    # Verify it was safety-blocked and returned empty subtasks list immediately
    assert len(subtasks) == 0
    decomposer.model_orch.complete_task.assert_not_called()

@pytest.mark.asyncio
async def test_safety_guardrail_allows_malicious_keywords_with_safe_intent():
    """Verify that a dangerous keyword with safe intent (e.g. backup) is allowed."""
    decomposer = GoalDecomposer()
    decomposer.model_orch = AsyncMock()
    
    mock_plan = {
        "plan": [
            {
                "step_id": "step_0",
                "agent_id": "architect",
                "prompt": "Backup database and prune obsolete data safely.",
                "is_complex": False,
                "dependencies": []
            }
        ]
    }
    decomposer.model_orch.complete_task.return_value = MagicMock(content=json.dumps(mock_plan))
    
    subtasks = await decomposer.decompose(
        title="veritabanını yedekle ve eski logları sil",
        description="Perform system logging backup and delete database entries older than 30 days",
        available_agents=[{"id": "architect", "name": "Architect", "role": "architect"}]
    )
    
    assert len(subtasks) == 1
    decomposer.model_orch.complete_task.assert_called_once()

@pytest.mark.asyncio
async def test_safety_guardrail_bypass_override():
    """Verify that environment variable bypass override allows any operation."""
    decomposer = GoalDecomposer()
    decomposer.model_orch = AsyncMock()
    
    mock_plan = {
        "plan": [
            {
                "step_id": "step_0",
                "agent_id": "architect",
                "prompt": "Bypassed execution forced.",
                "is_complex": False,
                "dependencies": []
            }
        ]
    }
    decomposer.model_orch.complete_task.return_value = MagicMock(content=json.dumps(mock_plan))
    
    # Enable bypass environment variable
    with patch.dict(os.environ, {"AGI_BYPASS_SAFETY_GUARDRAIL": "true"}):
        subtasks = await decomposer.decompose(
            title="sistem verilerini sil",
            description="Force deletion of all systems",
            available_agents=[{"id": "architect", "name": "Architect", "role": "architect"}]
        )
        
        assert len(subtasks) == 1
        decomposer.model_orch.complete_task.assert_called_once()
