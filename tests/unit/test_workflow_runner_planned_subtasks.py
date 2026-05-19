from services.orchestration.domain.models import GovernedTask
from libs.workflow.runner import _planned_subtask_spec, _planned_subtask_title


def test_planned_subtask_spec_accepts_governed_task_without_title():
    task = GovernedTask(
        id="gt-1",
        agent_id="architect",
        prompt="STRATEJIK ALT-GOREV: Draft repair plan\nDetails",
        complexity_reasoning="Draft repair plan",
        dependencies=["dep-1"],
    )

    spec = _planned_subtask_spec(task)

    assert spec == {
        "agent_id": "architect",
        "prompt": "STRATEJIK ALT-GOREV: Draft repair plan\nDetails",
        "title": "Draft repair plan",
        "dependencies": ["dep-1"],
    }


def test_planned_subtask_title_falls_back_to_prompt_first_line():
    class PromptOnlyTask:
        prompt = "STRATEJIK ALT-GOREV: Investigate failure\nMore context"

    assert _planned_subtask_title(PromptOnlyTask()) == "Investigate failure"
