import pytest
import asyncio
import os
from core.orchestrator import Orchestrator
from db.models import Project, ProjectStatus
from db.session import AsyncSessionLocal
from sqlalchemy import select
from llm.model_orchestrator import ModelOrchestrator

@pytest.mark.asyncio
async def test_budget_guardrail_enforcement():
    """
    Phase 7: Cok dusuk butceli bir projenin engellenmesini test eder.
    """
    orch = Orchestrator()
    await orch.start()
    
    title = "Budget Test Project"
    desc = "This should fail because of low budget."
    
    async with AsyncSessionLocal() as db:
        from db.models import Project
        from sqlalchemy import insert
        import uuid
        
        project_id_raw = uuid.uuid4()
        
        await db.execute(
            insert(Project).values(
                id=project_id_raw,
                title=title,
                description=desc,
                budget_limit=0.000001,
                status="pending",
                total_cost=0.5
            )
        )
        await db.commit()
        project_id = str(project_id_raw)

    # Orkestratoru calistir
    mo = ModelOrchestrator()
    
    with pytest.raises(PermissionError) as excinfo:
        await mo.complete_task(
            agent_role="architect",
            prompt="Hello",
            system_prompt="Be a bot",
            project_id=project_id
        )
    
    assert "Bütçe Aşıldı" in str(excinfo.value)
    print("\n[OK] Phase 7: Butce bariyeri basariyla yakalandi.")

@pytest.mark.asyncio
async def test_dynamic_specialist_creation():
    """
    Phase 8: Olmayan bir ajanin otomatik uretilmesini test eder.
    """
    orch = Orchestrator()
    await orch.start()
    
    agent_id = "Swift-Metal-Expert-Test"
    prompt = "Write a Metal shader in Swift."
    
    # Kütüphanede olmadıgından emin olalım
    from core.agency.loader import agency_loader
    if agent_id in agency_loader.agents:
        # Temizlik
        del agency_loader.agents[agent_id]
        dyn_path = os.path.join(agency_loader.base_dir, "dynamic", f"{agent_id}.md")
        if os.path.exists(dyn_path):
            os.remove(dyn_path)

    # Subtask uret (Orchestrator._run_subtask'i direkt test edelim)
    from core.task_management import SubTask
    from unittest.mock import AsyncMock, patch
    
    st = SubTask(id="st-1", agent_id=agent_id, prompt=prompt)
    
    # Mock LLM for dynamic creation
    mock_response = """
    {
      "name": "Swift Expert",
      "role": "iOS Developer",
      "emoji": "🧠",
      "system_prompt": "You are a Swift expert.",
      "category": "mobile"
    }
    """
    
    with patch.object(ModelOrchestrator, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        
        # Mock Agent.execute to avoid real subtask run after creation
        from agents.agent_registry import Agent
        from llm.model_orchestrator import LLMResponse
        
        with patch.object(Agent, "execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = LLMResponse(
                content='{"summary": "OK", "decisions": [], "risks": [], "next_actions": [], "deliverables": []}',
                provider="mock", model_name="mock", input_tokens=10, output_tokens=10, latency_s=0.1, cost_usd=0.0
            )
            
            await orch._run_subtask(st, project_id="test-proj-id")
    
    # Kontroller
    assert agent_id in orch._agents
    assert os.path.exists(os.path.join(agency_loader.base_dir, "dynamic", f"{agent_id}.md"))
    print(f"\n[OK] Phase 8: Dinamik ajan '{agent_id}' basariyla uretildi.")

if __name__ == "__main__":
    # Direkt calistirma destegi
    asyncio.run(test_budget_guardrail_enforcement())
    asyncio.run(test_dynamic_specialist_creation())
