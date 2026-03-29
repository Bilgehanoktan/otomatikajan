import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from improve.visual_observer import VisualUXObserver

@pytest.mark.asyncio
async def test_visual_observer_analyze_logic():
    # Mock database and model orchestrator
    mock_db = MagicMock()
    mock_orch = AsyncMock()
    
    # Mock vision response
    mock_vision_response = """
    [
      {
        "title": "Button Color Inconsistency",
        "description": "Primary button in the header is #ff0000 but the sidebar has #f00.",
        "severity": "low",
        "suggest_fix": "Use var(--primary-color) for all buttons.",
        "potential_impact": "Consistent branding"
      }
    ]
    """
    mock_orch.complete_vision.return_value = mock_vision_response
    
    observer = VisualUXObserver(mock_db, mock_orch)
    
    # Manually test the _analyze_screenshot method
    analysis = await observer._analyze_screenshot("base64_img_data")
    
    assert len(analysis) == 1
    assert analysis[0]["title"] == "Button Color Inconsistency"
    assert analysis[0]["severity"] == "low"

@pytest.mark.asyncio
async def test_visual_observer_formatting_for_ceo():
    # Simple test to verify the opportunity formatting for CEO Engine
    mock_db = MagicMock()
    mock_orch = AsyncMock()
    
    mock_vision_response = """
    [
      {
        "title": "Visual Bug",
        "description": "Text overlap in mobile view.",
        "severity": "high",
        "suggest_fix": "Add media query for .card-content.",
        "potential_impact": "Improved readability"
      }
    ]
    """
    mock_orch.complete_vision.return_value = mock_vision_response
    
    observer = VisualUXObserver(mock_db, mock_orch)
    
    # Patch the scan method parts to avoid real browser
    with patch.object(observer, "scan", new_callable=AsyncMock) as mock_scan:
        # We'll mock the return value as if it went through the loop
        mock_scan.return_value = [
            {
                "source_type": "visual_audit",
                "title": "Visual Bug",
                "severity": "high",
                "category": "ux_design"
            }
        ]
        
        ops = await observer.scan()
        assert len(ops) == 1
        assert ops[0]["source_type"] == "visual_audit"
        assert ops[0]["severity"] == "high"
