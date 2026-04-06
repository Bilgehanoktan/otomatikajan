from __future__ import annotations

from pathlib import Path

from packages.orchestration.agi.world.repo_graph import RepoGraph


def test_repo_graph_detects_local_edges_and_unresolved_imports(tmp_path: Path):
    (tmp_path / "core").mkdir()
    (tmp_path / "api").mkdir()
    (tmp_path / "core" / "utils.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
    (tmp_path / "core" / "main_logic.py").write_text(
        "from core.utils import ok\nfrom core.missing import nope\n", encoding="utf-8"
    )
    (tmp_path / "api" / "router.py").write_text(
        "from core.main_logic import ok\n", encoding="utf-8"
    )

    graph = RepoGraph(str(tmp_path))
    graph.scan()
    summary = graph.get_summary()

    assert "core/utils.py" in graph.local_edges["core/main_logic.py"]
    unresolved = summary["unresolved_local_imports"]
    assert any(item["path"] == "core/main_logic.py" for item in unresolved)
    assert "context_pack" in summary
    assert "entrypoints" in summary


def test_repo_graph_context_pack_contains_world_model_tokens(tmp_path: Path):
    (tmp_path / "main.py").write_text("import os\n", encoding="utf-8")
    graph = RepoGraph(str(tmp_path))
    graph.scan()

    pack = graph.export_context_pack()

    assert "[WORLD_MODEL]" in pack
    assert "entrypoints=" in pack
    assert "critical_files=" in pack
