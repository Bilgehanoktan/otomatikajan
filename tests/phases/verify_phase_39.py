import asyncio
import logging
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.orchestration.agi.governance.consensus_arbiter import ConsensusArbiter
from services.orchestration.agi.task_governance import GovernanceStatus, SovereignGoal, TaskPlanner

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("phase_39_verif")


async def test_sovereign_consensus_flow() -> bool:
    _log.info("Starting Phase 39 Verification: Sovereign Consensus & Multi-Agent Coordination...")

    planner = TaskPlanner()
    title = "Refactor Core Auth API"
    desc = "This task modifies the core authentication logic."

    strategic_tasks = [
        {
            "task_id": "phase39_security_review",
            "agent_id": "security",
            "objective": "modify core authentication logic safely",
            "acceptance_criteria": ["Consensus review is required for high-risk auth changes"],
            "dependencies": [],
        }
    ]

    with patch(
        "services.orchestration.agi.cognitive.recursive_decomposer.RecursiveDecomposer.decompose_goal",
        AsyncMock(return_value=strategic_tasks),
    ):
        subtasks = await planner.plan_sovereign(title, desc)

    high_risk_tasks = [st for st in subtasks if st.consensus_required]
    if not high_risk_tasks:
        _log.error("FAILURE: No tasks marked for consensus despite high-risk keywords.")
        return False
    _log.info("SUCCESS: Detected %s tasks requiring consensus.", len(high_risk_tasks))

    mock_consensus = {
        "consensus_score": 0.95,
        "hybrid_plan": "Consensus Plan: Security verified refactor.",
        "synthesis_logic": "Architect and Security agreement.",
        "points_of_agreement": ["Use JWT", "Enable MFA"],
        "residual_risks": [],
    }

    model_orch = SimpleNamespace(
        complete_task=AsyncMock(
            side_effect=[
                SimpleNamespace(content="Architect plan: apply compatible auth refactor."),
                SimpleNamespace(content="Security plan: verify token handling and MFA."),
            ]
        )
    )
    arbiter = ConsensusArbiter(model_orch=model_orch)

    parent = SovereignGoal(id="p39", title=title, status=GovernanceStatus.RUNNING)
    parent.subtasks = subtasks

    with patch(
        "services.orchestration.agi.governance.consensus_arbiter.consensus_manager.resolve",
        AsyncMock(return_value=mock_consensus),
    ):
        accepted, report = await arbiter.execute_debate(high_risk_tasks[0], context="Phase 39 verification")

    if not accepted or report.get("consensus_score") != 0.95:
        _log.error("FAILURE: Consensus arbiter did not accept the mocked high-confidence report.")
        return False

    _log.info("SUCCESS: Consensus Arbiter accepted the high-confidence report.")
    _log.info("Phase 39 Verification COMPLETED.")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(test_sovereign_consensus_flow()) else 1)
