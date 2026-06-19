import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.repair.ui_evidence_runner import UIEvidenceRunner
from services.repair.ui_evidence_models import UIEvidenceRequest

@pytest.mark.asyncio
async def test_capture_evidence_mock():
    runner = UIEvidenceRunner(base_output_dir="tmp_test_outputs")
    request = UIEvidenceRequest(
        case_id="case-test-123",
        target_url="http://example.com"
    )

    with patch("services.repair.ui_evidence_runner.async_playwright") as mock_pw:
        # Mocking the chain: playwright -> chromium -> launch -> browser -> context -> page
        mock_playwright = AsyncMock()
        mock_pw.return_value.__aenter__.return_value = mock_playwright
        
        mock_browser = AsyncMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_page = AsyncMock()
        mock_page.on = MagicMock() # .on is a synchronous event listener registration
        mock_context.new_page.return_value = mock_page
        mock_page.url = "http://example.com"
        mock_page.title.return_value = "Example Domain"
        
        # Act
        evidence = await runner.capture_evidence(request)
        
        # Assert
        assert evidence.case_id == "case-test-123"
        assert evidence.page_url == "http://example.com"
        assert evidence.page_title == "Example Domain"
        assert mock_page.goto.called
        assert mock_page.screenshot.called
        assert mock_context.tracing.start.called
        assert mock_context.tracing.stop.called

def test_get_mock_evidence():
    runner = UIEvidenceRunner()
    evidence = runner.get_mock_evidence("case-999")
    
    assert evidence.case_id == "case-999"
    assert evidence.screenshot_path is not None
    assert "mock_screenshot.png" in evidence.screenshot_path
    assert len(evidence.console_logs) == 2
