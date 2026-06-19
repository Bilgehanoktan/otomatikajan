from services.repair.code_localizer import localize_code
from services.repair.repair_models import RepairCase


def test_localizer_scores_traceback_file_highest():
    case = RepairCase(
        incident_id="INC-LOC",
        failed_test="tests/repair/test_code_localizer.py::test_localizer_scores_traceback_file_highest",
        traceback='File "services/repair/repair_case_builder.py", line 20, in build_repair_case',
        related_logs=["related log mentions services/repair/risk_adapter.py"],
        allowed_paths=["services/", "tests/"],
        forbidden_paths=["services/auth/"],
    )

    results = localize_code(case)

    assert results[0]["file"] == "services/repair/repair_case_builder.py"
    assert results[0]["score"] >= 50
    assert "traceback" in results[0]["reasons"]
