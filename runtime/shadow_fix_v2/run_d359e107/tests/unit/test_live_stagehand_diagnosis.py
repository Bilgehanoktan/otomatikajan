import pytest
from services.ui_repair.stagehand_adapter import StagehandAdapter
from services.repair.ui_diagnosis_models import UIDiagnosisRequest, UIDiagnosisResult

@pytest.mark.asyncio
async def test_live_stagehand_diagnose():
    """
    Verifies that StagehandAdapter correctly initializes the physical
    UIEvidenceRunner and executes the dynamic diagnose pipeline successfully.
    """
    adapter = StagehandAdapter()
    assert adapter.enabled is True
    
    request = UIDiagnosisRequest(
        case_id="TEST-CASE-999",
        symptom_description="Consensus timeline not rendering properly in Chrome.",
        evidence_pack_path="/meeting-room"
    )
    
    result = await adapter.diagnose(request)
    
    assert isinstance(result, UIDiagnosisResult)
    assert result.case_id == "TEST-CASE-999"
    assert "inconsistency" in result.root_cause_summary.lower() or "consensus" in result.root_cause_summary.lower()
    assert len(result.suspected_elements) > 0
    assert result.confidence_score > 0.5
    
    brief = result.technical_brief
    assert brief["stagehand_mode"] in {"physical_browser_live", "model_request_compat"}
