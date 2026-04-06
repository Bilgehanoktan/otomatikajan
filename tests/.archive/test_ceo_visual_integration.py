import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.ceo_engine import CEOEngine
from packages.persistence.models import ImprovementOpportunity

@pytest.mark.asyncio
async def test_ceo_engine_picks_up_visual_audit():
    # Setup
    mock_orch = AsyncMock()
    ceo = CEOEngine(mock_orch)
    
    # Mock visual observer to return 1 opportunity
    mock_visual_op = {
        "source_type": "visual_audit",
        "source_ref": "ui_scan_2024",
        "title": "Fix Button UI",
        "description": "Buttons are too square.",
        "severity": "medium",
        "category": "ux_design",
        "evidence_detail": '{"suggested_fix": "border-radius: 8px;"}'
    }
    
    # Mocking the session and scan
    # CEOEngine uses session_scope from packages.persistence.session
    with patch("core.ceo_engine.session_scope") as mock_session_scope:
        mock_session = AsyncMock()
        mock_session_scope.return_value.__aenter__.return_value = mock_session
        
        # Mocking observers
        with patch("packages.improvement_engine.visual_observer.VisualUXObserver.scan", new_callable=AsyncMock) as mock_visual_scan:
            mock_visual_scan.return_value = [mock_visual_op]
            
            with patch("packages.improvement_engine.observer.ImprovementObserver.scan", new_callable=AsyncMock) as mock_improve_scan:
                mock_improve_scan.return_value = []
                
                # Mock everything below the scan to avoid database or other complex internal calls hanging
                with patch("core.ceo_engine.CostRepository") as mock_cost_repo:
                    mock_cost_repo.total_cost = AsyncMock(return_value=0)
                    with patch.object(ceo, "_get_repair_health_summary", return_value={}):
                        with patch("core.ceo_engine.CEOForecaster.detect_anomalies", new_callable=AsyncMock) as mock_forecast:
                            mock_forecast.return_value = []
                            with patch.object(ceo, "score_opportunities", new_callable=AsyncMock) as mock_score:
                                mock_score.return_value = []
                                with patch.object(ceo, "_persist_opportunities", new_callable=AsyncMock) as mock_persist:
                                    with patch.object(ceo, "decide_next_actions", new_callable=AsyncMock) as mock_decide:
                                        
                                        await ceo.run_scan()
                                    
                                    # Verify scan was called
                                    assert mock_visual_scan.called
                                    # Verify opportunities were passed correctly (this is internal but good to check)
                                    # Since we mock score_opportunities, we check it
                                    assert mock_score.called
                                    ops_to_score = mock_score.call_args[0][0]
                                    assert any(op.get("source_type") == "visual_audit" for op in ops_to_score)
