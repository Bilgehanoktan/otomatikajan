import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.repair.ui_repair_orchestrator import UIRepairOrchestrator

@pytest.mark.asyncio
async def test_ui_repair_orchestrator_flow():
    orchestrator = UIRepairOrchestrator()
    
    with patch.object(orchestrator.evidence_runner, "capture_evidence", new_callable=AsyncMock) as mock_evidence:
        with patch.object(orchestrator.diagnosis_adapter, "diagnose", new_callable=AsyncMock) as mock_diag:
            with patch.object(orchestrator.pr_agent, "run_full_review_cycle", new_callable=AsyncMock) as mock_review:
                
                # Mock responses
                mock_evidence.return_value = MagicMock(screenshot_path="path/to/shot.png")
                mock_diag.return_value = MagicMock(root_cause_summary="Button is broken", suspected_elements=[])
                mock_review.return_value = MagicMock(governance_decision="PASSED")
                
                # Mock backend
                orchestrator.backend = MagicMock()
                orchestrator.backend.generate_patch.return_value = MagicMock(confidence=0.9, changed_files=["app.tsx"])
                
                # Run
                result = await orchestrator.run_full_repair_cycle("case-123", "http://local.test")
                
                # Assert
                assert result["case_id"] == "case-123"
                assert result["final_status"] == "PASSED"
                
                # Verify work_dir was passed
                args, kwargs = orchestrator.backend.generate_patch.call_args
                assert "work_dir" in kwargs
                assert "repair_outputs/case-123/sandbox" in kwargs["work_dir"]

@pytest.mark.asyncio
async def test_ui_repair_orchestrator_blocked_flow():
    orchestrator = UIRepairOrchestrator()
    
    with patch.object(orchestrator.evidence_runner, "capture_evidence", new_callable=AsyncMock) as mock_evidence:
        with patch.object(orchestrator.diagnosis_adapter, "diagnose", new_callable=AsyncMock) as mock_diag:
            # Mock responses
            mock_evidence.return_value = MagicMock(screenshot_path="path/to/shot.png")
            mock_diag.return_value = MagicMock(root_cause_summary="Safety issue", suspected_elements=[])
            
            # Mock backend as blocked (missing work_dir simulation or policy)
            orchestrator.backend = MagicMock()
            orchestrator.backend.generate_patch.return_value = MagicMock(
                exit_status="blocked", 
                agent_summary="Sandbox required"
            )
            
            # Run
            result = await orchestrator.run_full_repair_cycle("case-blocked", "http://local.test")
            
            # Assert
            assert result["final_status"] == "DRAFT_PR_BLOCKED_SANDBOX_REQUIRED"
            assert "Sandbox required" in result["detail"]
