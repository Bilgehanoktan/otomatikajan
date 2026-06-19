from services.repair.repair_case_builder import build_repair_case


def test_traceback_payload_builds_repair_case():
    case = build_repair_case(
        {
            "incident_id": "INC-100",
            "trace_id": "TRACE-100",
            "error_type": "AssertionError",
            "summary": "failed unit",
            "failed_command": "python -m pytest tests/repair/test_x.py",
            "failed_test": "tests/repair/test_x.py::test_y",
            "traceback": "File \"services/repair/code_localizer.py\", line 12, in localize_code",
            "related_logs": ["log line"],
        }
    )

    assert case.incident_id == "INC-100"
    assert case.trace_id == "TRACE-100"
    assert case.traceback
    assert "services/" in case.allowed_paths
    assert "services/auth/" in case.forbidden_paths
