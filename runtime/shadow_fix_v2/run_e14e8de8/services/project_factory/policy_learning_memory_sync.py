from typing import Dict, Any, Optional
from services.project_factory.models import PolicyLearningMemorySync, PolicyLearningSignal

def build_policy_learning_memory_sync(proposal_id: str, workspace_root: Optional[str] = None) -> PolicyLearningMemorySync:
    """
    Constructs the learning memory sync artifact.
    Crucially, it guarantees no actual memory files are modified.
    """
    
    # We produce synthetic signals based on the completed lifecycle.
    # In a full system, this would read from the actual PR agent analysis and scorecard.
    signals = [
        PolicyLearningSignal(
            type="policy_hardening_completed",
            summary="Policy proposal completed full governance cycle without production apply.",
            confidence=0.95,
            target_files=[]
        )
    ]
    
    sync_obj = PolicyLearningMemorySync(
        status="POLICY_LEARNING_SYNCED",
        proposal_id=proposal_id,
        source="policy_autopilot_final_release",
        signals=signals,
        write_mode="artifact_only",
        memory_files_modified=False
    )
    
    return sync_obj
