from pathlib import Path

def test_event_bus_supports_local_mode():
    content = Path("core/events.py").read_text(encoding="utf-8")
    assert 'EVENT_BUS_MODE' in content
    assert 'if EVENT_BUS_MODE == "local"' in content
