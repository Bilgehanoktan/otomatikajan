import pytest
from services.project_factory.policy_learning_memory_sync import build_policy_learning_memory_sync

def test_build_policy_learning_memory_sync():
    proposal_id = "POL-PF-001"
    sync_obj = build_policy_learning_memory_sync(proposal_id)
    
    assert sync_obj.status == "POLICY_LEARNING_SYNCED"
    assert sync_obj.proposal_id == "POL-PF-001"
    assert sync_obj.write_mode == "artifact_only"
    assert sync_obj.memory_files_modified is False
    assert len(sync_obj.signals) > 0
    assert sync_obj.signals[0].type == "policy_hardening_completed"
