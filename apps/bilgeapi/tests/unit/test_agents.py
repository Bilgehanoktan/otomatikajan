import os
import pytest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy import select

from bilgeapi.agents.analyst_agent import AnalystAgent
from bilgeapi.agents.security_agent import SecurityAgent
from bilgeapi.agents.tester_agent import TesterAgent
from bilgeapi.agents.reviewer_agent import ReviewerAgent
from bilgeapi.agents.ceo_agent import CeoAgent

from bilgeapi.llm.base import LLMResult
from bilgeapi.llm.router import LLMRouter
from bilgeapi.security.secret_scanner import SecretScanner
from bilgeapi.governance.policy_engine import PolicyEngine
from bilgeapi.governance.risk_engine import RiskEngine
from bilgeapi.execution.file_executor import FileExecutor
from bilgeapi.execution.rollback_manager import RollbackManager
from bilgeapi.execution.quarantine import QuarantineManager
from bilgeapi.orchestration.task_queue import TaskQueue
from bilgeapi.integrations.telegram import TelegramBridge
from bilgeapi.governance.approval_engine import ApprovalEngine

from bilgeapi.memory.db import init_workspace_db, get_workspace_db_session, _engines
from bilgeapi.memory.repositories import SystemRepository, TaskRepository, ApprovalRepository
from bilgeapi.core.workspace import WorkspaceManager

@pytest.fixture
async def mock_workspace(monkeypatch):
    """
    Async fixture that overrides WorkspaceManager to use a temporary directory
    for the database, initializes the schema, and disposes of all engines on cleanup.
    """
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()
        
        def mock_init(self, *args, **kwargs):
            self.start_path = tmp_path
            self.project_root = tmp_path
            self.workspace_dir = tmp_path
            
        monkeypatch.setattr(WorkspaceManager, "__init__", mock_init)
        
        await init_workspace_db(tmp_path)
        
        yield tmp_path
        
        # Clean up database engines to prevent file locking on Windows
        from bilgeapi.memory.db import _engines
        for eng in list(_engines.values()):
            await eng.dispose()
        _engines.clear()

async def setup_ceo_agent(tmp_path, router):
    # 1. Initialize system
    async with get_workspace_db_session(tmp_path) as session:
        sys_repo = SystemRepository(session)
        system = await sys_repo.create_or_update(
            system_name="CEO Test System",
            project_type="Python",
            root_path=str(tmp_path),
            health_score=100.0
        )
        system_id = system["id"]
        
    # 2. Risk rules and Policy Engine
    risk_rules = [
        {"path_pattern": "**/auth/*", "risk_level": "HIGH", "reason": "Auth path is sensitive"},
        {"path_pattern": "**/settings.py", "risk_level": "HIGH", "reason": "Settings file"}
    ]
    risk_eng = RiskEngine(risk_rules)
    
    permissions = {
        "permissions": {
            "allow": ["Read", "Grep", "Write", "Edit", "Rename"],
            "ask": [],
            "deny": ["sudo *"]
        }
    }
    delete_policy = {
        "policy": {
            "forbidden": ["**/.git/**/*"],
            "approval_required": ["**/settings.py"]
        }
    }
    task_policy = {
        "policy": {
            "max_concurrency": 2,
            "retry_limit": 3,
            "low_risk_auto_execute": True
        }
    }
    policy_eng = PolicyEngine(permissions, delete_policy, task_policy, risk_eng)
    
    # 3. FileExecutor
    rollback_mgr = RollbackManager(tmp_path, tmp_path / ".bilgeapi")
    quar_manager = QuarantineManager(tmp_path, tmp_path / ".bilgeapi")
    scanner = SecretScanner()
    executor = FileExecutor(tmp_path, tmp_path / ".bilgeapi", policy_eng, rollback_mgr, quar_manager, scanner)
    
    # 4. TaskQueue & TelegramBridge
    queue = TaskQueue()
    telegram = TelegramBridge(scanner)
    
    # 5. CeoAgent
    ceo = CeoAgent(
        workspace_dir=tmp_path,
        policy_engine=policy_eng,
        file_executor=executor,
        task_queue=queue,
        telegram_bridge=telegram,
        router=router,
        secret_scanner=scanner
    )
    
    return ceo, system_id, queue

@pytest.mark.asyncio
async def test_analyst_agent_structured_output():
    router = LLMRouter("mock")
    scanner = SecretScanner()
    agent = AnalystAgent(router, scanner)
    
    # Preset JSON output
    router.provider.preset_response = """
    {
        "summary": "FastAPI workspace structure",
        "discovered_issues": ["No test files found in apps/"],
        "suggestions": ["Add unit tests"],
        "next_recommended_tasks": ["Create test_sample.py"]
    }
    """
    
    res = await agent.analyze_system(["apps/main.py"], 80.0)
    assert res["summary"] == "FastAPI workspace structure"
    assert "No test files found in apps/" in res["discovered_issues"]
    assert "Add unit tests" in res["suggestions"]
    assert "Create test_sample.py" in res["next_recommended_tasks"]

@pytest.mark.asyncio
async def test_security_agent_risk_parsing():
    router = LLMRouter("mock")
    scanner = SecretScanner()
    agent = SecurityAgent(router, scanner)
    
    router.provider.preset_response = """
    {
        "risk_level": "LOW",
        "risk_score": 2.5,
        "reasons": ["Non-critical utility script modified"],
        "requires_approval": false,
        "recommended_action": "ALLOW"
    }
    """
    
    res = await agent.evaluate_risk("Write", "src/utils.py", "def new_util(): pass")
    assert res["risk_level"] == "LOW"
    assert res["risk_score"] == 2.5
    assert "Non-critical utility script modified" in res["reasons"]
    assert res["requires_approval"] is False
    assert res["recommended_action"] == "ALLOW"

@pytest.mark.asyncio
async def test_tester_agent_report_parsing():
    router = LLMRouter("mock")
    scanner = SecretScanner()
    agent = TesterAgent(router, scanner)
    
    router.provider.preset_response = """
    {
        "summary": "All 10 tests passed successfully.",
        "failures": [],
        "coverage_score": 88.5,
        "missing_test_recommendations": ["Add integration test for task routing"]
    }
    """
    
    res = await agent.analyze_test_results("collected 10 items\n10 passed")
    assert res["summary"] == "All 10 tests passed successfully."
    assert len(res["failures"]) == 0
    assert res["coverage_score"] == 88.5
    assert "Add integration test for task routing" in res["missing_test_recommendations"]

@pytest.mark.asyncio
async def test_reviewer_agent_diff_parsing():
    router = LLMRouter("mock")
    scanner = SecretScanner()
    agent = ReviewerAgent(router, scanner)
    
    router.provider.preset_response = """
    {
        "summary": "Removed deprecated config endpoint",
        "quality_score": 8.5,
        "cleanliness_recommendations": ["Clean up unused imports", "Format dictionary parameters"],
        "security_flags": []
    }
    """
    
    res = await agent.review_diff("--- a/config.py\n+++ b/config.py")
    assert res["summary"] == "Removed deprecated config endpoint"
    assert res["quality_score"] == 8.5
    assert "cleanliness_recommendations" in res
    assert "Clean up unused imports" in res["cleanliness_recommendations"]
    assert len(res["security_flags"]) == 0

@pytest.mark.asyncio
async def test_malformed_llm_output_handling():
    # 1. BaseAgent _parse_json_safely
    router = LLMRouter("mock")
    scanner = SecretScanner()
    agent = SecurityAgent(router, scanner)
    
    # Test BaseAgent regex fallback with extra text
    router.provider.preset_response = """
    Here is the JSON you requested:
    ```json
    {
        "risk_level": "LOW",
        "risk_score": 1.5,
        "reasons": ["Safe"],
        "requires_approval": false,
        "recommended_action": "ALLOW"
    }
    ```
    I hope this helps!
    """
    res = await agent.evaluate_risk("Write", "src/utils.py", "code")
    assert res["risk_level"] == "LOW"
    assert res["risk_score"] == 1.5
    
    # Test completely malformed text
    router.provider.preset_response = "Plain text response that is not JSON at all."
    res = await agent.evaluate_risk("Write", "src/utils.py", "code")
    
    # Should escalate to CRITICAL/BLOCK due to malformed output
    assert res["risk_level"] == "CRITICAL"
    assert res["risk_score"] == 10.0
    assert res["requires_approval"] is True
    assert res["recommended_action"] == "BLOCK"
    assert any("Malformed security agent" in reason or "Malformed JSON" in reason for reason in res["reasons"])

@pytest.mark.asyncio
async def test_secret_redaction_in_agent_outputs():
    router = LLMRouter("mock")
    scanner = SecretScanner()
    agent = SecurityAgent(router, scanner)
    
    # Preset output containing sensitive information
    router.provider.preset_response = """
    {
        "risk_level": "LOW",
        "risk_score": 1.5,
        "reasons": ["Checking password = 'super_secret_token_123'"],
        "requires_approval": false,
        "recommended_action": "ALLOW"
    }
    """
    
    res = await agent.evaluate_risk("Write", "src/utils.py", "code")
    assert "super_secret_token_123" not in str(res)
    assert "[MASKED_SECRET]" in str(res)

@pytest.mark.asyncio
async def test_low_risk_task_auto_flow(mock_workspace):
    tmp_path = mock_workspace
    router = LLMRouter("mock")
    
    # Preset responses
    # SecurityAgent evaluate_risk
    router.provider.preset_response = """
    {
        "risk_level": "LOW",
        "risk_score": 1.0,
        "reasons": ["Safe low-risk write"],
        "requires_approval": false,
        "recommended_action": "ALLOW"
    }
    """
    
    ceo, system_id, queue = await setup_ceo_agent(tmp_path, router)
    
    async with get_workspace_db_session(tmp_path) as session:
        task = await queue.enqueue(
            system_id=system_id,
            title="Update utility script",
            agent_role="specialist",
            action_type="WRITE",
            risk_level="LOW",
            payload={"file": "src/utils.py", "content": "def run(): print('low risk')"},
            session=session
        )
        task_id = task["id"]
        
    async with get_workspace_db_session(tmp_path) as session:
        # Run via CeoAgent
        res = await ceo.run_task(task_id, session)
        assert res["status"] == "COMPLETED"
        assert res["executor_result"]["status"] == "SUCCESS"
        
    # Verify file was written
    target_file = tmp_path / "src" / "utils.py"
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "def run(): print('low risk')"
    
    # Verify task status is COMPLETED in DB
    async with get_workspace_db_session(tmp_path) as session:
        task_repo = TaskRepository(session)
        updated_task = await task_repo.get_task(task_id)
        assert updated_task["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_high_risk_task_blocked_and_sent_to_approval(mock_workspace):
    tmp_path = mock_workspace
    router = LLMRouter("mock")
    
    # Preset SecurityAgent response to HIGH risk
    router.provider.preset_response = """
    {
        "risk_level": "HIGH",
        "risk_score": 8.0,
        "reasons": ["Touching sensitive settings file"],
        "requires_approval": true,
        "recommended_action": "BLOCK"
    }
    """
    
    ceo, system_id, queue = await setup_ceo_agent(tmp_path, router)
    
    async with get_workspace_db_session(tmp_path) as session:
        task = await queue.enqueue(
            system_id=system_id,
            title="Edit configuration",
            agent_role="specialist",
            action_type="WRITE",
            risk_level="HIGH",
            payload={"file": "src/settings.py", "content": "DEBUG = False"},
            session=session
        )
        task_id = task["id"]
        
    async with get_workspace_db_session(tmp_path) as session:
        res = await ceo.run_task(task_id, session)
        assert res["status"] == "BLOCKED"
        assert "Requires human approval" in res["reason"]
        assert "approval_id" in res
        
    # Verify task status in DB is BLOCKED
    async with get_workspace_db_session(tmp_path) as session:
        task_repo = TaskRepository(session)
        updated_task = await task_repo.get_task(task_id)
        assert updated_task["status"] == "BLOCKED"
        
        # Verify approval request was created
        app_repo = ApprovalRepository(session)
        pending = await app_repo.get_pending_approvals()
        assert len(pending) == 1
        assert pending[0]["task_id"] == task_id

@pytest.mark.asyncio
async def test_approved_high_risk_task_resumes(mock_workspace, monkeypatch):
    tmp_path = mock_workspace
    router = LLMRouter("mock")
    
    # Configure environment for approval validation
    monkeypatch.setenv("BILGEAPI_TELEGRAM_CHAT_ID", "999888")
    
    # Preset SecurityAgent response to HIGH risk
    router.provider.preset_response = """
    {
        "risk_level": "HIGH",
        "risk_score": 8.0,
        "reasons": ["Touching sensitive settings file"],
        "requires_approval": true,
        "recommended_action": "BLOCK"
    }
    """
    
    ceo, system_id, queue = await setup_ceo_agent(tmp_path, router)
    
    async with get_workspace_db_session(tmp_path) as session:
        task = await queue.enqueue(
            system_id=system_id,
            title="Edit configuration",
            agent_role="specialist",
            action_type="WRITE",
            risk_level="HIGH",
            payload={"file": "src/settings.py", "content": "DEBUG = False"},
            session=session
        )
        task_id = task["id"]
        
    # 1. First run blocks the task
    async with get_workspace_db_session(tmp_path) as session:
        res = await ceo.run_task(task_id, session)
        assert res["status"] == "BLOCKED"
        approval_id = res["approval_id"]
        
    # 2. Verify task status is BLOCKED
    async with get_workspace_db_session(tmp_path) as session:
        task_repo = TaskRepository(session)
        t = await task_repo.get_task(task_id)
        assert t["status"] == "BLOCKED"
        
        app_repo = ApprovalRepository(session)
        pending = await app_repo.get_pending_approvals()
        approval_record = pending[0]
        token = approval_record["token"]
        action_hash = approval_record["action_hash"]

    # 3. Submit approval through ApprovalEngine
    async with get_workspace_db_session(tmp_path) as session:
        await ApprovalEngine.validate_and_submit_approval(
            approval_id=approval_id,
            token=token,
            status="APPROVED",
            chat_id="999888",
            action_hash=action_hash,
            approved_by="test_user",
            session=session
        )
        await session.commit()
        
    # 4. Verify task status has changed to PENDING_APPROVED
    async with get_workspace_db_session(tmp_path) as session:
        task_repo = TaskRepository(session)
        t = await task_repo.get_task(task_id)
        assert t["status"] == "PENDING_APPROVED"

    # 5. Run CeoAgent again for the task
    async with get_workspace_db_session(tmp_path) as session:
        res2 = await ceo.run_task(task_id, session)
        assert res2["status"] == "COMPLETED"
        
    # Verify file was written
    target_file = tmp_path / "src" / "settings.py"
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "DEBUG = False"

@pytest.mark.asyncio
async def test_ceo_report_generation(mock_workspace):
    tmp_path = mock_workspace
    router = LLMRouter("mock")
    
    # Preset Analyst response
    router.provider.preset_response = """
    {
        "summary": "Project status summary containing sensitive password = 'secret-passwd'",
        "discovered_issues": ["Issue"],
        "suggestions": ["Suggestion"],
        "next_recommended_tasks": ["Task"]
    }
    """
    
    ceo, system_id, queue = await setup_ceo_agent(tmp_path, router)
    
    # Enqueue a couple of tasks to populate the report counts
    async with get_workspace_db_session(tmp_path) as session:
        await queue.enqueue(
            system_id=system_id,
            title="Task 1",
            agent_role="specialist",
            action_type="WRITE",
            risk_level="LOW",
            payload={"file": "src/utils.py", "content": "123"},
            session=session
        )
        
    async with get_workspace_db_session(tmp_path) as session:
        report = await ceo.generate_ceo_report(session)
        
        # Verify fields in the CEO report
        assert "system_summary" in report
        assert "discovered_issues" in report
        assert "risk_levels" in report
        assert "actions_taken" in report
        assert "blocked_actions" in report
        assert "approval_requests" in report
        assert "next_recommended_tasks" in report
        
        # Verify secret redaction inside report content
        report_str = str(report)
        assert "secret-passwd" not in report_str
        assert "[MASKED_SECRET]" in report_str
