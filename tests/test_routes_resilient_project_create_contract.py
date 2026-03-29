from pathlib import Path

def test_create_project_has_db_fallback():
    content = Path("api/task_write_router.py").read_text(encoding="utf-8")
    assert "Görev kuyruğa alınamadı, ancak DB'ye kaydedildi." in content
    assert "try:" in content
