from services.repair.repair_case_builder import build_repair_case
from services.repair.repair_plan_builder import build_repair_plan


def test_repair_plan_is_created_before_patch_generation():
    case = build_repair_case(
        {
            "incident_id": "INC-PLAN",
            "failed_command": "pytest tests/repair/test_repair_plan_builder.py",
            "summary": "plan test",
        }
    )

    plan = build_repair_plan(case, [{"file": "services/repair/repair_case_builder.py"}])

    assert plan.incident_id == "INC-PLAN"
    assert plan.target_files == ["services/repair/repair_case_builder.py"]
    assert plan.expected_tests == ["pytest tests/repair/test_repair_plan_builder.py"]
    assert plan.forbidden_actions

