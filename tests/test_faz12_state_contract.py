from pathlib import Path


def test_active_debates_should_not_be_process_local_only() -> None:
    src = Path("api/faz12_router.py").read_text(encoding="utf-8")

    assert "_ACTIVE_DEBATES = []" not in src, (
        "Debate state process-local tutuluyor; restart sonrası kaybolur."
    )
    assert "ACTIVE_DEBATES_KEY =" in src
    assert "get_redis_client()" in src
