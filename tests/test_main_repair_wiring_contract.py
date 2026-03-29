from pathlib import Path

def test_main_uses_model_orch_for_repair_wiring():
    content = Path("main.py").read_text(encoding="utf-8")
    assert 'model_orch=getattr(orchestrator, "model_orch", None)' in content
    assert '_llm' not in content
