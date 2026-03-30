from core.agi.prompt_blueprints import (
    build_backend_agi_prompt,
    build_planner_execution_contract,
    build_ui_agi_prompt,
)
from core.agi.schemas import ContextPackage, ProblemFrame, RiskLevel, TaskType


def test_backend_prompt_contains_memory_preservation_rule():
    blueprint = build_backend_agi_prompt(
        product_name="Bilgehan AGI",
        mission="Repo üzerinde güvenli, izlenebilir otonom geliştirme yap",
        repo_context="core/orchestrator.py is critical",
    )

    assert "append-only" in blueprint.body
    assert "Do not delete prior memory" in blueprint.body
    assert "half-integrations" in blueprint.body


def test_ui_prompt_contains_honest_mission_control_sections():
    blueprint = build_ui_agi_prompt(
        product_name="Bilgehan AGI",
        mission="Gerçek sistem durumunu dürüstçe göster",
    )

    assert "Mission control overview" in blueprint.body
    assert "No fake charts" in blueprint.body
    assert "world model" in blueprint.body.lower()


def test_planner_contract_exposes_world_model_and_json_schema():
    frame = ProblemFrame(
        task_type=TaskType.ANALYSIS,
        objective="Fix planning quality",
        risk_level=RiskLevel.MEDIUM,
        constraints=["Do not delete memory"],
        evidence_required=["tests", "diff"],
    )
    context = ContextPackage(
        working_context="Investigate orchestrator traceability",
        relevant_skills=["architect", "backend_dev"],
        graph_links=[{
            "hubs": [{"path": "core/agi/orchestrator.py", "dependents_count": 4}],
            "critical": ["core/agi/orchestrator.py"],
            "entrypoints": ["main.py"],
            "unresolved_local_imports": [],
            "cycles": [],
        }],
    )

    prompt = build_planner_execution_contract(frame, context)

    assert "WORLD MODEL SUMMARY" in prompt
    assert "Return ONLY valid JSON" in prompt
    assert "Do not delete prior memory" in prompt
