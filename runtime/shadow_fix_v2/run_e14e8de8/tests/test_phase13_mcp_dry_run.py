import asyncio
import logging
from libs.mcp.server import MCPServer
from libs.workflow.engine import WorkflowEngine
from libs.workflow.models import WorkflowInstance, WorkflowStep, WorkflowStatus, StepStatus
from libs.workflow.persistence import WorkflowPersistence

# Logları konsolda görmek için
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger("mcp_workflow_bridge")

async def mock_plan_step(context: dict, **kwargs):
    logger.info("  [Action] 'plan' running...")
    await asyncio.sleep(0.5)
    return {"_context_update": {"plan_ready": True}, "output": "Plan created successfully"}

async def mock_execute_step(context: dict, **kwargs):
    if not context.get("plan_ready"):
        raise ValueError("Cannot execute without a plan!")
    logger.info(f"  [Action] 'execute' running for repo {kwargs.get('repo_url')}...")
    await asyncio.sleep(1.0)
    return {"output": "Execution completed", "lines_changed": 150}

class MockPersistence:
    def __init__(self):
        self.instances = {}
        self.events = {}
        self.steps = {}

    async def save_instance(self, instance):
        self.instances[instance.id] = instance

    async def load_instance(self, project_id):
        return self.instances.get(project_id)

    async def save_step(self, w_id, step):
        if w_id not in self.steps:
            self.steps[w_id] = {}
        self.steps[w_id][step.id] = step

    async def save_event(self, project_id, event_type, step_id=None, payload=None, operator_id="system"):
        if project_id not in self.events:
            self.events[project_id] = []
        self.events[project_id].append({
            "event_type": event_type,
            "step_id": step_id,
            "payload": payload,
            "operator_id": operator_id
        })

    async def load_history(self, project_id):
        return self.events.get(project_id, [])

async def setup_dry_run():
    # 1. Workflow Engine'i hazırlayalım (db olmadan çalışması için mock)
    engine = WorkflowEngine()
    engine.persistence = MockPersistence()
    
    engine.register_action("plan_subtasks", mock_plan_step)
    engine.register_action("execute_subtasks", mock_execute_step)

    # 2. MCP (Model Context Protocol) Sunucusunu ayağa kaldıralım
    # Ajanlar ("LLM'ler") bu sunucu üzerinden araç bulacaktır.
    mcp = MCPServer(name="sovereign-core-mcp")

    # 3. MCP üzerinden "Workflow Başlatma (StartWorkflow)" aracı tanımlanıyor.
    async def mcp_start_workflow_handler(project_id: str, repo_url: str):
        logger.info(f"[MCP-Inbound] LLM requested workflow for Project: {project_id}")
        
        import uuid
        
        # Basit bir 2-adımlı DAG oluşturuyoruz: plan_subtasks -> execute_subtasks
        step1 = WorkflowStep(
            id=str(uuid.uuid4()),
            action="plan_subtasks",
            name="Plan Phase",
            input_data={"project_id": project_id}
        )
        step2 = WorkflowStep(
            id=str(uuid.uuid4()),
            action="execute_subtasks",
            name="Execution Phase",
            dependencies=[step1.id], # step2 expects step1 to finish
            input_data={"repo_url": repo_url}
        )
        
        instance = WorkflowInstance(
            id=str(uuid.uuid4()),
            workflow_type="project_lifecycle",
            steps=[step1, step2],
            context={}
        )
        
        # Engine'e verelim ve çalıştıralım (Normalde background task olarak atılır)
        await engine.execute(instance)
        
        return {
            "instance_id": str(instance.id),
            "final_status": instance.status.value,
            "steps_results": [
                {"step_name": s.name, "status": s.status.value, "error": s.error}
                for s in instance.steps
            ]
        }

    mcp.register_tool(
        name="start_workflow",
        description="Starts a durable workflow for a given project ID using Sovereign DAG.",
        input_schema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "repo_url": {"type": "string"}
            },
            "required": ["project_id", "repo_url"]
        },
        handler=mcp_start_workflow_handler
    )

    # --- SİMÜLASYON BAŞLIYOR ---

    # Ajan (örn: Claude 3.5 Sonnet) geldi, MCP'ye "Senin hangi tool'ların var?" diye sordu:
    tools_available = mcp.list_tools()
    logger.info(f"[Agent] Acquired tools from MCP: {[t['name'] for t in tools_available]}")

    # Ajan, elde ettiği şemaya göre çalıştırıyor (start_workflow)
    logger.info("[Agent] Decided to trigger 'start_workflow' tool via LLM JSON call...")
    
    # MCP aracı çalıştırıyor ve Engine'e bağlanıyor:
    mcp_result = await mcp.call_tool("start_workflow", {"project_id": "proj_123456", "repo_url": "github.com/test/repo"})
    
    logger.info(f"\n[Agent] Received final result from MCP:\n{mcp_result}")

if __name__ == "__main__":
    asyncio.run(setup_dry_run())
