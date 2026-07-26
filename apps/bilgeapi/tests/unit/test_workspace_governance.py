import os
import pytest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from bilgeapi.memory.db import init_workspace_db, get_workspace_db_session
from bilgeapi.memory.repositories import (
    SystemRepository, TaskRepository, EventLogRepository,
    AuditLogRepository, DecisionRepository, ApprovalRepository,
    QuarantineItemRepository
)
from bilgeapi.governance.audit_logger import WorkspaceAuditLogger
from bilgeapi.governance.risk_engine import RiskEngine
from bilgeapi.governance.policy_engine import PolicyEngine
from bilgeapi.security.path_guard import PathGuard
from bilgeapi.security.secret_scanner import SecretScanner
from bilgeapi.execution.quarantine import QuarantineManager
from bilgeapi.execution.rollback_manager import RollbackManager
from bilgeapi.execution.safe_delete import SafeDelete
from bilgeapi.execution.diff_manager import DiffManager
from bilgeapi.execution.file_executor import FileExecutor

@pytest.mark.asyncio
async def test_workspace_governance_flow():
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()
        
        # 1. Initialize workspace db
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        await init_workspace_db(tmp_path)
        db_file = memory_dir / "bilgeapi.db"
        assert db_file.exists()
        
        # 2. Test repositories within a session context
        async with get_workspace_db_session(tmp_path) as session:
            sys_repo = SystemRepository(session)
            task_repo = TaskRepository(session)
            event_repo = EventLogRepository(session)
            audit_repo = AuditLogRepository(session)
            dec_repo = DecisionRepository(session)
            app_repo = ApprovalRepository(session)
            quar_repo = QuarantineItemRepository(session)
            
            # Test System Repository
            system = await sys_repo.create_or_update(
                system_name="Test System",
                project_type="Python",
                root_path=str(tmp_path),
                health_score=95.5,
                metadata_fields={"env": "test"}
            )
            assert system["system_name"] == "Test System"
            assert system["health_score"] == 95.5
            
            system_get = await sys_repo.get_by_root(str(tmp_path))
            assert system_get["id"] == system["id"]
            
            # Test Task Repository
            task = await task_repo.create_task(
                system_id=system["id"],
                title="Test Task",
                description="A simple test task",
                agent_role="CEO",
                action_type="Write",
                status="PENDING",
                risk_level="LOW",
                payload={"file": "test.txt"}
            )
            assert task["title"] == "Test Task"
            assert task["attempt_count"] == 0
            
            updated_task = await task_repo.update_task_status(task["id"], "RUNNING", attempt_increment=True)
            assert updated_task["status"] == "RUNNING"
            assert updated_task["attempt_count"] == 1
            
            tasks = await task_repo.list_tasks(system["id"])
            assert len(tasks) == 1
            assert tasks[0]["id"] == task["id"]
            
            # Test Event Log Repository
            event = await event_repo.log_event(system["id"], "SCAN_COMPLETED", "Project scan successful")
            assert event["event_type"] == "SCAN_COMPLETED"
            
            events = await event_repo.list_events(system["id"])
            assert len(events) == 1
            assert events[0]["message"] == "Project scan successful"
            
            # Test Audit Log Repository
            audit = await audit_repo.log_audit(
                event_type="FILE_EDITED",
                actor_id="agent_123",
                actor_type="AI_AGENT",
                action="Edit",
                target="config.py",
                status="ALLOWED",
                risk_level="MEDIUM"
            )
            assert audit["event_type"] == "FILE_EDITED"
            assert audit["status"] == "ALLOWED"
            
            audits = await audit_repo.list_recent_audits()
            assert len(audits) == 1
            
            # Test Decision Repository
            decision = await dec_repo.record_decision(
                task_id=task["id"],
                classification="REPAIR",
                risk_score=2.5,
                risk_level="LOW",
                eligibility="ELIGIBLE",
                requires_human_gate=False,
                decision_reason="Safe auto-execute task",
                reasons=["Risk score is below threshold", "No protected files touched"]
            )
            assert decision["risk_level"] == "LOW"
            assert decision["requires_human_gate"] is False
            
            dec_get = await dec_repo.get_decision_by_task(task["id"])
            assert dec_get["id"] == decision["id"]
            
            # Test Approval Repository
            from datetime import datetime, timedelta
            approval = await app_repo.request_approval(
                task["id"],
                decision["id"],
                "EXECUTE_CONFIRM",
                token="test_token_123",
                action_hash="sha256_mock_hash",
                expires_at=datetime.utcnow() + timedelta(minutes=15)
            )
            assert approval["status"] == "PENDING"
            
            pendings = await app_repo.get_pending_approvals()
            assert len(pendings) == 1
            
            approved = await app_repo.submit_approval(approval["id"], "APPROVED", "Checked ok", "admin")
            assert approved["status"] == "APPROVED"
            assert approved["approved_by"] == "admin"
            
            # Test Quarantine Repository
            quar_item = await quar_repo.quarantine_file(
                filepath="old_backup.bak",
                original_hash="sha256_123",
                quarantine_path="quarantine/old_backup.bak",
                reason="Temporary backup deletion"
            )
            assert quar_item["restored"] is False
            
            restored = await quar_repo.restore_file(quar_item["id"])
            assert restored["restored"] is True

        # 3. Test WorkspaceAuditLogger
        logger_instance = WorkspaceAuditLogger(tmp_path)
        logged = await logger_instance.log_action(
            event_type="FILE_DELETED",
            actor_id="user_admin",
            actor_type="HUMAN",
            action="Delete",
            target="secret_keys.pem",
            status="DENIED",
            risk_level="CRITICAL",
            before_state={"sensitive_key": "some_secret_token", "public_info": "hello"},
            after_state=None
        )
        assert logged is not None
        assert logged["status"] == "DENIED"
        
        # Verify JSONL file was written and redacted
        audit_jsonl = tmp_path / "audit" / "audit.jsonl"
        assert audit_jsonl.exists()
        
        with open(audit_jsonl, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1
            log_data = json.loads(lines[0])
            assert log_data["event_type"] == "FILE_DELETED"
            assert log_data["before_state"]["sensitive_key"] == "[REDACTED]"
            assert log_data["before_state"]["public_info"] == "hello"

        # 4. Test RiskEngine
        risk_rules = [
            {"path_pattern": "**/auth/*", "risk_level": "HIGH", "reason": "Auth path is sensitive"},
            {"path_pattern": "**/*.cfg", "risk_level": "MEDIUM", "reason": "Config path is medium risk"},
            {"path_pattern": "**/*.bak", "risk_level": "MEDIUM", "reason": "Backup path is medium risk"}
        ]
        risk_eng = RiskEngine(risk_rules)
        
        # Test normal path
        level, score, reason = risk_eng.evaluate_path("src/utils.py")
        assert level == "LOW"
        assert score == 1.0
        
        # Test pattern match
        level, score, reason = risk_eng.evaluate_path("src/auth/login.py")
        assert level == "HIGH"
        assert score == 7.0
        assert "Auth path" in reason
        
        # Test traversal protection
        level, score, reason = risk_eng.evaluate_path("src/../.env")
        assert level == "CRITICAL"
        assert score == 10.0
        assert "traversal" in reason.lower()
        
        # Test protected path (.git, .bilgeapi, .env, keys, database)
        level, score, reason = risk_eng.evaluate_path("project/.bilgeapi/config.yaml")
        assert level == "CRITICAL"
        assert score == 10.0
        assert "protected" in reason.lower()
        
        level, score, reason = risk_eng.evaluate_path(".env.production")
        assert level == "CRITICAL"
        assert score == 10.0
        
        level, score, reason = risk_eng.evaluate_path("keys/server.key")
        assert level == "CRITICAL"
        assert score == 10.0
        
        level, score, reason = risk_eng.evaluate_path("database/sqlite.db")
        assert level == "CRITICAL"
        assert score == 10.0

        # 5. Test PolicyEngine
        permissions = {
            "permissions": {
                "allow": ["Read", "Grep", "Write", "Edit", "Rename"],
                "ask": [],
                "deny": ["sudo *", "rm -rf *"]
            }
        }
        delete_policy = {
            "policy": {
                "forbidden": ["**/.git/**/*", "**/.bilgeapi/**/*"],
                "approval_required": ["**/settings.py", "**/package.json"],
                "quarantine": ["**/*.bak"],
                "auto_delete": ["**/__pycache__/*"]
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
        
        # Test ALLOW file action
        decision_read = policy_eng.decide_file_action("Read", "src/utils.py")
        assert decision_read["decision"] == "ALLOW"
        assert decision_read["risk_level"] == "LOW"
        
        # Test DENY file action due to protected target
        decision_env = policy_eng.decide_file_action("Write", ".env")
        assert decision_env["decision"] == "DENY"
        assert decision_env["risk_level"] == "CRITICAL"
        
        # Test APPROVAL_REQUIRED file action (e.g. Write config)
        decision_write = policy_eng.decide_file_action("Write", "src/auth/login.py")
        assert decision_write["decision"] == "APPROVAL_REQUIRED"
        assert decision_write["risk_level"] == "HIGH"
        
        # Test Deletion Policy - Forbidden deletion
        decision_del_git = policy_eng.decide_file_action("Delete", "src/.git/config")
        assert decision_del_git["decision"] == "DENY"
        
        # Test Deletion Policy - Approval required deletion
        decision_del_settings = policy_eng.decide_file_action("Delete", "src/settings.py")
        assert decision_del_settings["decision"] == "APPROVAL_REQUIRED"
        assert decision_del_settings["risk_level"] == "HIGH"
        
        # Test Deletion Policy - Auto delete
        decision_del_cache = policy_eng.decide_file_action("Delete", "src/__pycache__/utils.pyc")
        assert decision_del_cache["decision"] == "ALLOW"
        
        # Test command evaluation - Allowed command
        decision_cmd_grep = policy_eng.decide_command_action("grep 'hello' src/utils.py")
        assert decision_cmd_grep["decision"] == "ALLOW"
        
        # Test command evaluation - Denied command
        decision_cmd_sudo = policy_eng.decide_command_action("sudo systemctl restart nginx")
        assert decision_cmd_sudo["decision"] == "DENY"
        assert decision_cmd_sudo["risk_level"] == "CRITICAL"
        
        # Test command evaluation - Unspecified command
        decision_cmd_unspec = policy_eng.decide_command_action("python script.py")
        assert decision_cmd_unspec["decision"] == "APPROVAL_REQUIRED"
        assert decision_cmd_unspec["risk_level"] == "HIGH"
        
        # Test task policy execution - ALLOW low risk
        task_exec_low = policy_eng.decide_task_execution("LOW", 0)
        assert task_exec_low["decision"] == "ALLOW"
        
        # Test task policy execution - DENY retry limit exceeded
        task_exec_retry = policy_eng.decide_task_execution("LOW", 3)
        assert task_exec_retry["decision"] == "DENY"
        
        # Test task policy execution - APPROVAL_REQUIRED high risk
        task_exec_high = policy_eng.decide_task_execution("HIGH", 1)
        assert task_exec_high["decision"] == "APPROVAL_REQUIRED"

        # 6. Test PathGuard
        guard = PathGuard(tmp_path)
        res_path = guard.validate_and_resolve("src/utils.py")
        assert res_path == tmp_path / "src" / "utils.py"
        with pytest.raises(ValueError, match="traversal"):
            guard.validate_and_resolve("src/../../env")
        with pytest.raises(ValueError, match="protected"):
            guard.validate_and_resolve(".git/config")
        with pytest.raises(ValueError, match="protected"):
            guard.validate_and_resolve(".bilgeapi/system.yaml")

        # 7. Test SecretScanner
        scanner = SecretScanner()
        masked_txt = scanner.scan_and_mask("password = 'my-secret-key-123'")
        assert "[MASKED_SECRET]" in masked_txt
        masked_url = scanner.scan_and_mask("postgres://user:super_pass_123@localhost:5432/db")
        assert "[MASKED_CREDENTIALS]" in masked_url

        # 8. Test QuarantineManager
        dummy_file = tmp_path / "dummy.bak"
        dummy_file.write_text("dummy backup data", encoding="utf-8")
        
        quar_manager = QuarantineManager(tmp_path, tmp_path / ".bilgeapi")
        async with get_workspace_db_session(tmp_path) as session:
            quar_rec = await quar_manager.quarantine_file("dummy.bak", "Test quarantine", session)
            assert quar_rec["filepath"] == "dummy.bak"
            assert not dummy_file.exists()
            
            restored_rec = await quar_manager.restore_file(quar_rec["id"], session)
            assert restored_rec["restored"] is True
            assert dummy_file.exists()
            assert dummy_file.read_text(encoding="utf-8") == "dummy backup data"

        # 9. Test RollbackManager
        rollback_mgr = RollbackManager(tmp_path, tmp_path / ".bilgeapi")
        target_file = tmp_path / "target.txt"
        target_file.write_text("original content", encoding="utf-8")
        
        backup_path = rollback_mgr.create_backup("target.txt")
        assert backup_path is not None
        
        target_file.write_text("modified content", encoding="utf-8")
        rollback_mgr.restore_backup("target.txt", backup_path)
        assert target_file.read_text(encoding="utf-8") == "original content"
        
        rollback_mgr.remove_backup(backup_path)
        assert not (tmp_path / backup_path).exists()

        # 10. Test DiffManager
        diff_mgr = DiffManager(scanner)
        diff_output = diff_mgr.generate_diff("target.txt", "password = 'secret'\nvalue = 1", "password = 'new_secret'\nvalue = 2")
        assert "[MASKED_SECRET]" in diff_output
        assert "target.txt" in diff_output

        # 11. Test SafeDelete
        safe_del = SafeDelete(tmp_path, tmp_path / ".bilgeapi", quar_manager, policy_eng)
        
        cache_dir = tmp_path / "src" / "__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        pyc_file = cache_dir / "test.pyc"
        pyc_file.write_text("some bytecode", encoding="utf-8")
        
        async with get_workspace_db_session(tmp_path) as session:
            del_res = await safe_del.delete_file("src/__pycache__/test.pyc", session)
            assert del_res["action"] == "DIRECT_DELETE"
            assert not pyc_file.exists()

        bak_file = tmp_path / "src" / "old_backup.bak"
        bak_file.write_text("backup data", encoding="utf-8")
        
        async with get_workspace_db_session(tmp_path) as session:
            del_res = await safe_del.delete_file("src/old_backup.bak", session)
            assert del_res["action"] == "QUARANTINE"
            assert not bak_file.exists()

        high_file = tmp_path / "src" / "settings.py"
        high_file.write_text("settings content", encoding="utf-8")
        async with get_workspace_db_session(tmp_path) as session:
            with pytest.raises(PermissionError, match="requires human approval"):
                await safe_del.delete_file("src/settings.py", session)

        crit_file = tmp_path / ".env"
        crit_file.write_text("ENVVAR=val", encoding="utf-8")
        async with get_workspace_db_session(tmp_path) as session:
            with pytest.raises(ValueError, match="DENIED by policy"):
                await safe_del.delete_file(".env", session)

        # 12. Test FileExecutor
        executor = FileExecutor(tmp_path, tmp_path / ".bilgeapi", policy_eng, rollback_mgr, quar_manager, scanner)
        
        write_res = executor.write_file("src/allowed.txt", "API_KEY = 'secret-key-456'")
        assert write_res["status"] == "SUCCESS"
        written_file = tmp_path / "src" / "allowed.txt"
        assert written_file.exists()
        assert "[MASKED_SECRET]" in written_file.read_text(encoding="utf-8")
        
        patch_res = executor.patch_file(
            "src/allowed.txt", 
            "API_KEY = '[MASKED_SECRET]'", 
            "API_KEY = 'new-secret-789'"
        )
        assert patch_res["status"] == "SUCCESS"
        assert "[MASKED_SECRET]" in written_file.read_text(encoding="utf-8")
        
        rename_res = executor.rename_file("src/allowed.txt", "src/renamed.txt")
        assert rename_res["status"] == "SUCCESS"
        assert not written_file.exists()
        assert (tmp_path / "src" / "renamed.txt").exists()

        # Cleanup database engine to avoid file locking on Windows
        from bilgeapi.memory.db import get_workspace_engine, _engines
        engine = get_workspace_engine(tmp_path)
        await engine.dispose()
        _engines.clear()


@pytest.mark.asyncio
async def test_telegram_approval_system(monkeypatch):
    import unittest.mock
    from datetime import datetime, timezone, timedelta
    from httpx import AsyncClient
    from tempfile import TemporaryDirectory
    from pathlib import Path
    
    from bilgeapi.main import app
    from bilgeapi.memory.db import init_workspace_db, get_workspace_db_session, get_workspace_engine, _engines
    from bilgeapi.memory.repositories import (
        SystemRepository, TaskRepository, DecisionRepository, ApprovalRepository, AuditLogRepository
    )
    from bilgeapi.integrations.telegram import TelegramBridge
    from bilgeapi.governance.approval_engine import ApprovalEngine
    from bilgeapi.core.workspace import WorkspaceManager

    # Set up mock environment variables
    monkeypatch.setenv("BILGEAPI_TELEGRAM_CHAT_ID", "123456")
    monkeypatch.setenv("BILGEAPI_TELEGRAM_BOT_TOKEN", "mock_bot_token")
    monkeypatch.setenv("BILGEAPI_TELEGRAM_WEBHOOK_SECRET", "mock_webhook_secret")

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()
        
        # Override WorkspaceManager __init__ to use tmp_path
        # so routers will use our temporary database instead of default workspace
        def mock_init(self, *args, **kwargs):
            self.start_path = tmp_path
            self.project_root = tmp_path
            self.workspace_dir = tmp_path
        monkeypatch.setattr(WorkspaceManager, "__init__", mock_init)
        
        await init_workspace_db(tmp_path)
        
        async with get_workspace_db_session(tmp_path) as session:
            sys_repo = SystemRepository(session)
            task_repo = TaskRepository(session)
            dec_repo = DecisionRepository(session)
            app_repo = ApprovalRepository(session)
            audit_repo = AuditLogRepository(session)
            
            # 1. Setup mock records
            system = await sys_repo.create_or_update(
                system_name="Approval Test System",
                project_type="Python",
                root_path=str(tmp_path),
                health_score=100.0
            )
            
            task = await task_repo.create_task(
                system_id=system["id"],
                title="Sensitive Deletion Task",
                description="Removing key config",
                agent_role="CEO",
                action_type="Delete",
                status="BLOCKED",
                risk_level="HIGH",
                payload={"file": "settings.py"}
            )
            
            decision = await dec_repo.record_decision(
                task_id=task["id"],
                classification="DELETION",
                risk_score=8.5,
                risk_level="HIGH",
                eligibility="APPROVAL_REQUIRED",
                requires_human_gate=True,
                decision_reason="Deleting high risk config settings.py",
                reasons=["Settings file deletion requires approval"]
            )
            
            task_id = task["id"]
            decision_id = decision["id"]
            action_hash = "mock_hash_12345"

        # 2. Test Telegram Message Redaction
        bridge = TelegramBridge()
        
        mock_response = unittest.mock.AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = unittest.mock.Mock()
        
        # Mock httpx AsyncClient post
        with unittest.mock.patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            # Send approval request with sensitive data inside description
            await bridge.send_approval_request(
                approval_id="mock_app_id",
                title="Delete DB config",
                description="password = 'my_super_secret_password'",
                token="mock_token_key_here",
                risk_level="HIGH",
                risk_score=8.5,
                reasons=["token = 'super_token_123'"],
                action_hash="mock_hash_12345"
            )
            
            # Verify mock POST payload has masked secret
            assert mock_post.called
            call_kwargs = mock_post.call_args[1]
            payload = call_kwargs.get("json", {})
            text = payload.get("text", "")
            
            assert "my_super_secret_password" not in text
            assert "super_token_123" not in text
            assert "[MASKED_SECRET]" in text or "[MASKED_CREDENTIALS]" in text

        # Test approvals endpoints via AsyncClient
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=30.0) as client:
            
            # --- Test Case: Valid Approval ---
            async with get_workspace_db_session(tmp_path) as session:
                approval = await ApprovalEngine.create_approval_request(
                    task_id=task_id,
                    decision_id=decision_id,
                    request_type="DELETE_CONFIRM",
                    action_hash=action_hash,
                    session=session
                )
                approval_id = approval["id"]
                token = approval["token"]
            
            # Direct submit approval
            res = await client.post(
                f"/v1/workspace/approvals/{approval_id}/submit",
                json={
                    "token": token,
                    "status": "APPROVED",
                    "chat_id": "123456",
                    "action_hash": action_hash,
                    "approved_by": "operator_bob"
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 200
            assert res.json()["verdict"] == "APPROVED"
            
            # Verify DB updates
            async with get_workspace_db_session(tmp_path) as session:
                from sqlalchemy import select
                from bilgeapi.memory.models import ApprovalModel, TaskModel
                
                db_app = (await session.execute(select(ApprovalModel).where(ApprovalModel.id == approval_id))).scalar_one()
                assert db_app.status == "APPROVED"
                assert db_app.approved_by == "operator_bob"
                
                db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task_id))).scalar_one()
                assert db_task.status == "PENDING_APPROVED"

            # --- Test Case: Valid Rejection ---
            # Create a new approval request for rejection test
            async with get_workspace_db_session(tmp_path) as session:
                task_rej = await TaskRepository(session).create_task(
                    system_id=system["id"],
                    title="Reject target",
                    description="Rejected path",
                    agent_role="CEO",
                    action_type="Delete",
                    status="BLOCKED",
                    risk_level="HIGH"
                )
                dec_rej = await DecisionRepository(session).record_decision(
                    task_id=task_rej["id"],
                    classification="DELETION",
                    risk_score=8.5,
                    risk_level="HIGH",
                    eligibility="APPROVAL_REQUIRED",
                    requires_human_gate=True,
                    decision_reason="Requires approval",
                    reasons=[]
                )
                approval_rej = await ApprovalEngine.create_approval_request(
                    task_id=task_rej["id"],
                    decision_id=dec_rej["id"],
                    request_type="DELETE_CONFIRM",
                    action_hash="rej_hash",
                    session=session
                )
                app_rej_id = approval_rej["id"]
                token_rej = approval_rej["token"]
            
            res = await client.post(
                f"/v1/workspace/approvals/{app_rej_id}/submit",
                json={
                    "token": token_rej,
                    "status": "REJECTED",
                    "chat_id": "123456",
                    "action_hash": "rej_hash",
                    "approved_by": "operator_bob"
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 200
            assert res.json()["verdict"] == "REJECTED"
            
            async with get_workspace_db_session(tmp_path) as session:
                db_app = (await session.execute(select(ApprovalModel).where(ApprovalModel.id == app_rej_id))).scalar_one()
                assert db_app.status == "REJECTED"
                
                db_task = (await session.execute(select(TaskModel).where(TaskModel.id == task_rej["id"]))).scalar_one()
                # Task should remain BLOCKED
                assert db_task.status == "BLOCKED"

            # --- Test Case: Unauthorized Chat ID ---
            async with get_workspace_db_session(tmp_path) as session:
                approval_unauth = await ApprovalEngine.create_approval_request(
                    task_id=task_id,
                    decision_id=decision_id,
                    request_type="DELETE_CONFIRM",
                    action_hash=action_hash,
                    session=session
                )
                app_unauth_id = approval_unauth["id"]
                token_unauth = approval_unauth["token"]
            
            res = await client.post(
                f"/v1/workspace/approvals/{app_unauth_id}/submit",
                json={
                    "token": token_unauth,
                    "status": "APPROVED",
                    "chat_id": "999999", # Unauthorized
                    "action_hash": action_hash,
                    "approved_by": "malicious_user"
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 400
            assert "Unauthorized chat_id" in res.text

            # --- Test Case: Expired Token ---
            async with get_workspace_db_session(tmp_path) as session:
                approval_exp = await ApprovalEngine.create_approval_request(
                    task_id=task_id,
                    decision_id=decision_id,
                    request_type="DELETE_CONFIRM",
                    action_hash=action_hash,
                    session=session
                )
                # Manually expire in DB
                db_record = (await session.execute(select(ApprovalModel).where(ApprovalModel.id == approval_exp["id"]))).scalar_one()
                db_record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
                await session.flush()
                app_exp_id = approval_exp["id"]
                token_exp = approval_exp["token"]
            
            res = await client.post(
                f"/v1/workspace/approvals/{app_exp_id}/submit",
                json={
                    "token": token_exp,
                    "status": "APPROVED",
                    "chat_id": "123456",
                    "action_hash": action_hash,
                    "approved_by": "operator_bob"
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 400
            assert "Expired token" in res.text
            
            # Verify status is updated to EXPIRED in database
            async with get_workspace_db_session(tmp_path) as session:
                db_app = (await session.execute(select(ApprovalModel).where(ApprovalModel.id == app_exp_id))).scalar_one()
                assert db_app.status == "EXPIRED"

            # --- Test Case: Wrong Action Hash ---
            async with get_workspace_db_session(tmp_path) as session:
                approval_hash = await ApprovalEngine.create_approval_request(
                    task_id=task_id,
                    decision_id=decision_id,
                    request_type="DELETE_CONFIRM",
                    action_hash=action_hash,
                    session=session
                )
                app_hash_id = approval_hash["id"]
                token_hash = approval_hash["token"]
            
            res = await client.post(
                f"/v1/workspace/approvals/{app_hash_id}/submit",
                json={
                    "token": token_hash,
                    "status": "APPROVED",
                    "chat_id": "123456",
                    "action_hash": "wrong_hash_val",
                    "approved_by": "operator_bob"
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 400
            assert "Wrong action hash" in res.text

            # --- Test Case: Missing Approval ID ---
            res = await client.post(
                f"/v1/workspace/approvals/non_existent_approval_uuid/submit",
                json={
                    "token": "some_token",
                    "status": "APPROVED",
                    "chat_id": "123456",
                    "action_hash": action_hash,
                    "approved_by": "operator_bob"
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 400
            assert "Missing approval_id" in res.text

            # --- Test Case: Reused Token / Replay Protection ---
            # Reuse the first approved token
            res = await client.post(
                f"/v1/workspace/approvals/{approval_id}/submit",
                json={
                    "token": token,
                    "status": "APPROVED",
                    "chat_id": "123456",
                    "action_hash": action_hash,
                    "approved_by": "operator_bob"
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 400
            assert "Reused token" in res.text

            # --- Test Case: Invalid Status Transition ---
            # Manually set status to EXPIRED and try to approve it
            async with get_workspace_db_session(tmp_path) as session:
                approval_trans = await ApprovalEngine.create_approval_request(
                    task_id=task_id,
                    decision_id=decision_id,
                    request_type="DELETE_CONFIRM",
                    action_hash=action_hash,
                    session=session
                )
                db_record = (await session.execute(select(ApprovalModel).where(ApprovalModel.id == approval_trans["id"]))).scalar_one()
                db_record.status = "EXPIRED"
                await session.flush()
                app_trans_id = approval_trans["id"]
                token_trans = approval_trans["token"]
            
            res = await client.post(
                f"/v1/workspace/approvals/{app_trans_id}/submit",
                json={
                    "token": token_trans,
                    "status": "APPROVED",
                    "chat_id": "123456",
                    "action_hash": action_hash,
                    "approved_by": "operator_bob"
                },
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 400
            assert "Invalid status transition" in res.text

            # --- Test Case: Webhook Header Validation & Webhook Processing ---
            # 1. Missing header
            async with get_workspace_db_session(tmp_path) as session:
                approval_wh = await ApprovalEngine.create_approval_request(
                    task_id=task_id,
                    decision_id=decision_id,
                    request_type="DELETE_CONFIRM",
                    action_hash=action_hash,
                    session=session
                )
                app_wh_id = approval_wh["id"]
                token_wh = approval_wh["token"]
            
            import hmac
            import hashlib
            msg = f"{app_wh_id}:approve:{token_wh[:8]}"
            sig = hmac.new(b"mock_bot_token", msg.encode(), hashlib.sha256).hexdigest()[:32]

            webhook_payload = {
                "update_id": 98765,
                "callback_query": {
                    "id": "cb_id_111",
                    "from": {
                        "id": 123456,
                        "is_bot": False,
                        "first_name": "Bob",
                        "username": "operator_bob"
                    },
                    "message": {
                        "message_id": 999,
                        "chat": {
                            "id": 123456,
                            "type": "private"
                        },
                        "text": "Approval required..."
                    },
                    "data": f"approve:{app_wh_id}:{token_wh[:8]}:{sig}"
                }
            }
            
            res = await client.post(
                "/v1/telegram/webhook",
                json=webhook_payload
            )
            assert res.status_code == 403  # Header is missing!
            
            # 2. Wrong header token value
            res = await client.post(
                "/v1/telegram/webhook",
                json=webhook_payload,
                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"}
            )
            assert res.status_code == 403
            
            # 3. Correct header & success processing
            res = await client.post(
                "/v1/telegram/webhook",
                json=webhook_payload,
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 200
            assert res.json()["verdict"] == "APPROVED"
            
            # Verify DB status is APPROVED
            async with get_workspace_db_session(tmp_path) as session:
                db_app = (await session.execute(select(ApprovalModel).where(ApprovalModel.id == app_wh_id))).scalar_one()
                assert db_app.status == "APPROVED"
                assert db_app.approved_by == "operator_bob"
            
            # 4. Correct header but invalid callback signature
            bad_payload = webhook_payload.copy()
            # Tamper with the callback data to supply a wrong signature
            bad_payload["callback_query"] = webhook_payload["callback_query"].copy()
            bad_payload["callback_query"]["data"] = f"approve:{app_wh_id}:{token_wh[:8]}:badsignature"
            res = await client.post(
                "/v1/telegram/webhook",
                json=bad_payload,
                headers={"X-Telegram-Bot-Api-Secret-Token": "mock_webhook_secret"}
            )
            assert res.status_code == 403
            assert "Unauthorized callback signature" in res.text

        # Cleanup database engine to avoid file locking on Windows
        from bilgeapi.memory.db import _engines
        for eng in list(_engines.values()):
            await eng.dispose()
        _engines.clear()
