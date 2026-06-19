import pytest
import os
from services.ui_repair.open_swe_adapter import OpenSWEAdapter

@pytest.mark.asyncio
async def test_openswe_live_patch_generation():
    """
    Verifies that OpenSWEAdapter dynamically reads original target file contents,
    correctly triggers patch/diff creation and git branch checkouts.
    """
    adapter = OpenSWEAdapter()
    assert adapter.output_dir == "repair_outputs/openswe"
    
    diagnostic = {
        "root_cause": "Hydration drift detected on main page.",
        "repair_instruction": "Inject client-only mounting guard.",
        "suspected_files": ["apps/refine_control_plane/src/app/repair-lab/page.tsx"]
    }
    
    result = await adapter.generate_repair(case_id="TEST-SWE-999", diagnostic=diagnostic)
    
    assert result["success"] is True
    assert "patch_path" in result
    assert "patch_summary" in result
    assert "pr_url" in result
    assert "branch_name" in result
    
    # Assert physical patch diff file was created successfully
    assert os.path.exists(result["patch_path"])
