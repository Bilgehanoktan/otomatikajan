import pytest
import tempfile
from services.project_factory.policy_pr_agent_review import run_policy_pr_agent_review
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

@pytest.fixture
def workspace_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        p_dir = _resolve_policy_autopilot_dir(temp_dir)
        p_dir.mkdir(parents=True, exist_ok=True)
        yield temp_dir

def test_run_policy_pr_agent_review(workspace_dir):
    review = run_policy_pr_agent_review("POL-1", workspace_dir)
    assert review.status == "PASSED"
    assert review.proposal_id == "POL-1"
    assert len(review.suggestions) > 0
    
    # Verify artifact written
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    assert (p_dir / "policy_pr_agent_review.json").exists()
