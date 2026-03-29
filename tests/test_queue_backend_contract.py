from pathlib import Path


def test_job_queue_auto_mode_policy_should_match_runtime_rules() -> None:
    src = Path("core/job_queue.py").read_text(encoding="utf-8")

    assert "QUEUE_BACKEND" in src
    assert "create_job_queue" in src
    assert 'backend == "celery"' in src
    assert 'backend == "inprocess"' in src
